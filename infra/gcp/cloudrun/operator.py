"""Operator-only Cloud Shell tooling. Never imported by application containers."""
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import urllib.error
import urllib.request

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from infra.gcp.cloudrun import namespace as ns  # noqa: E402

Blocked, blocked = ns.Blocked, ns.blocked
PLAN = json.loads(Path(__file__).with_name("services.json").read_text())
APIS = [name + ".googleapis.com" for name in (
    "run", "aiplatform", "artifactregistry", "bigquery", "iamcredentials", "logging", "monitoring", "secretmanager")]
CHECKS = {"lint", "unit-contract", "architecture", "build", "secret-scan", "analyze", "CodeQL"}


def run(args):
    ns.command(args)
    result = subprocess.run(args, text=True, capture_output=True, cwd=ROOT, check=False)
    if result.returncode:
        blocked(" ".join(args[:3]), " ".join(args[3:]), result.stderr.strip() or result.stdout.strip(),
                "Review IAM/organization policy with the Google team; do not bypass it.")
    return result.stdout.strip()


def required(name, pattern):
    value = os.environ.get(name, "")
    if not re.fullmatch(pattern, value):
        blocked("configuration", name, "missing or invalid value", "Set the documented external variable.")
    return value


def config():
    cfg = dict(project=required("ITA_GCP_PROJECT", r"[a-z][a-z0-9-]{4,61}[a-z0-9]"),
                region=required("ITA_GCP_REGION", r"[a-z]+-[a-z]+[0-9]"))
    ns.scope(cfg)
    return cfg


def gc(cfg, *args):
    return run(["gcloud", *args, "--project="+cfg["project"], "--quiet"])


def account(cfg, service):
    return PLAN[service]["service_account"] + "@" + cfg["project"] + ".iam.gserviceaccount.com"


def prefix():
    return ns.prefix()


def service_name(service):
    return ns.name("service", prefix() + "-" + PLAN[service]["resource_suffix"])


def table_config():
    dataset = required("ITA_BIGQUERY_DATASET", r"[A-Za-z0-9_]{1,1024}")
    table = required("ITA_BIGQUERY_TABLE", r"[A-Za-z0-9_]{1,1024}")
    if (dataset, table) != ("hackathon_dados", "extrato_sintetico"):
        ns.deny("BigQuery source", "only the confirmed read-only source is authorized")
    return dataset, table


def preflight(cfg):
    failures = []
    def check(label, action):
        try:
            value = action()
            print(f"CONFIRMADO {label}: {value}")
            return value
        except Blocked as error:
            failures.append(label)
            print(error)
            return None
    check("tools", lambda: run(["docker", "version", "--format", "{{.Client.Version}} / {{.Server.Version}} "]))
    current = check("current project", lambda: run(["gcloud", "config", "get-value", "project"]))
    if current != cfg["project"]:
        failures.append("project mismatch")
        print("BLOCKED project mismatch: select the intended project manually before mutations.")
    check("active account", lambda: run(["gcloud", "auth", "list", "--filter=status:ACTIVE", "--format=value(account)"]))
    print("CONFIRMADO requested region: " + cfg["region"])
    enabled = check("enabled APIs", lambda: gc(cfg, "services", "list", "--enabled", "--format=value(config.name)"))
    if enabled is not None:
        missing = set(APIS) - set(enabled.splitlines())
        if missing:
            failures.append("required APIs")
            print("BLOCKED missing APIs: " + ",".join(sorted(missing)) + "; ask Google team; no automatic enable.")
        print("Cloud SQL/VPC Access not required; Agent Engine optional and unused.")
    dataset, table = table_config()
    resource = cfg["project"] + ":" + dataset + "." + table
    check("BigQuery table metadata", lambda: run(["bq", "--project_id="+cfg["project"], "show", "--format=prettyjson", resource]))
    # Dry run validates query access/schema without creating a query job or reading rows.
    query = f"SELECT id_usuario, vlr, saldo_apos FROM `{cfg['project']}.{dataset}.{table}` WHERE FALSE"
    check("BigQuery query access (dry run, no rows)", lambda: run(["bq", "--project_id="+cfg["project"], "query",
          "--location="+cfg["region"], "--use_legacy_sql=false", "--dry_run", query]))
    check("Vertex regional API (not generateContent)", lambda: gc(cfg, "ai", "models", "list", "--region="+cfg["region"], "--limit=1", "--format=json"))
    check("Artifact Registry", lambda: gc(cfg, "artifacts", "repositories", "list", "--location="+cfg["region"], "--format=json"))
    check("Cloud Run", lambda: gc(cfg, "run", "services", "list", "--region="+cfg["region"], "--format=json"))
    check("service accounts visibility", lambda: gc(cfg, "iam", "service-accounts", "list", "--format=json"))
    print("AINDA NÃO TESTADO: runtime SAs, signJwt, real Gemini/BQ journey, image push, deployment, ingress/org policy.")
    if failures:
        blocked("read-only preflight", cfg["project"], ", ".join(failures), "Send a sanitized report to the project maintainer/Google team.")
    print("PREPARED preflight PASS; no mutation authorized by this result alone.")


def repository(cfg, create=False):
    ns.scope(cfg)
    repo = ns.name("repository", os.getenv("ITA_ARTIFACT_REPOSITORY", prefix()))
    resource = f"projects/{cfg['project']}/locations/{cfg['region']}/repositories/{repo}"
    if create:
        current = run(["gcloud", "config", "get-value", "project"])
        if current != cfg["project"]:
            blocked("confirm project", resource, "active project differs", "Select the confirmed project manually; no mutation performed.")
        print(f"CONFIRMADO project={cfg['project']} region={cfg['region']}")
    repos = json.loads(gc(cfg, "artifacts", "repositories", "list", "--location="+cfg["region"], "--format=json"))
    matches = [r for r in repos if r["name"] == resource]
    if not matches:
        if not create:
            blocked("find repository", resource, "not found", "Run only artifact_repository.sh --apply when explicitly authorized; no shared fallback.")
        print("OPERATION CREATE Artifact Registry " + resource + " format=DOCKER immutable-tags=true", flush=True)
        gc(cfg, "artifacts", "repositories", "create", repo, "--repository-format=docker", "--location="+cfg["region"],
           "--immutable-tags", "--labels="+",".join(k+"="+v for k, v in ns.OWNER.items()))
    else:
        ns.labels(matches[0].get("labels", {}))
        if matches[0].get("format") != "DOCKER" or not matches[0].get("dockerConfig", {}).get("immutableTags"):
            blocked("select repository", resource, "format/tag policy mismatch", "Inspect manually; never modify or adopt an existing resource.")
        print("OWNED repository already exists; NO MUTATION: " + resource)
    return cfg["region"] + "-docker.pkg.dev/" + cfg["project"] + "/" + repo


def verify_account(cfg, service, detail):
    email = account(cfg, service)
    ns.account(email)
    if detail.get("email") != email or detail.get("description") != ns.SA_DESCRIPTION or detail.get("disabled"):
        blocked("verify service account", PLAN[service]["service_account"], "ownership/identity mismatch or disabled", "Review collision with Google team; never adopt an external identity.")


def identities(cfg):
    ns.scope(cfg)
    existing = {a["email"]: a for a in json.loads(gc(cfg, "iam", "service-accounts", "list", "--format=json"))}
    # Check every collision before creating any account. No project/table IAM writes.
    for service in PLAN:
        if account(cfg, service) in existing:
            verify_account(cfg, service, existing[account(cfg, service)])
    for service in PLAN:
        if account(cfg, service) not in existing:
            gc(cfg, "iam", "service-accounts", "create", ns.name("account", PLAN[service]["service_account"]),
               "--description="+ns.SA_DESCRIPTION)
    print("PREPARADO own accounts only; IAM NOT applied. Shared project/table remain READ_ONLY. Runtime permissions require a later explicit human decision.")


def verify_runtime_resources(cfg):
    for service in PLAN:
        detail = json.loads(gc(cfg, "iam", "service-accounts", "describe", account(cfg, service), "--format=json"))
        verify_account(cfg, service, detail)
    secret = ns.name("secret", required("ITA_IDENTITY_SECRET", r"[a-zA-Z0-9_-]{1,255}"))
    detail = json.loads(gc(cfg, "secrets", "describe", secret, "--format=json"))
    if detail.get("name") != "projects/"+cfg["project"]+"/secrets/"+secret:
        # Secret Manager returns numeric project identifiers; this package cannot infer them.
        # Resolve the selected short name with the explicit --project, then enforce ownership.
        if detail.get("name", "").split("/")[-1] != secret:
            ns.deny(secret, "secret identity mismatch")
    ns.labels(detail.get("labels", {}))


def certified_sha():
    sha = required("ITA_CERTIFIED_SHA", r"[0-9a-f]{40}")
    if run(["git", "rev-parse", "HEAD"]) != sha or run(["git", "status", "--porcelain"]):
        blocked("build", sha, "checkout differs or is dirty", "Use a clean checkout at the certified SHA.")
    def github(path):
        req = urllib.request.Request("https://api.github.com/repos/escossio/ita-agent-batalha/" + path,
                                     headers={"Accept": "application/vnd.github+json"})
        with urllib.request.urlopen(req, timeout=15) as response:
            return json.load(response)
    checks = github("commits/"+sha+"/check-runs?per_page=100")["check_runs"]
    # Latest completed check for each required name must succeed; pending fails closed.
    for name in CHECKS:
        candidates = [c for c in checks if c["name"] == name]
        latest = max(candidates, key=lambda c: c["id"]) if candidates else {}
        if latest.get("conclusion") != "success" or latest.get("status") != "completed":
            blocked("certification", sha, "required check not green: "+name, "Finish certification before building.")
    statuses = github("commits/"+sha+"/status")["statuses"]
    distributed = next((s for s in statuses if s["context"] == "distributed-foundation"), {})
    if distributed.get("state") != "success":
        blocked("certification", sha, "distributed-foundation not green", "Certify this exact SHA on a worker.")
    return sha


def artifact_path():
    path = Path(os.environ.get("ITA_DEPLOYMENT_MANIFEST", str(ROOT / ".artifacts/cloudrun/images.json"))).resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def build_push(cfg):
    sha = certified_sha()
    repo = repository(cfg)
    gc(cfg, "auth", "configure-docker", cfg["region"]+"-docker.pkg.dev")
    created = run(["git", "show", "-s", "--format=%cI", sha])
    records = []
    path = artifact_path()
    if path.exists():
        blocked("build manifest", str(path), "already exists", "Choose a new output path; do not overwrite provenance.")
    for service in PLAN:
        name, dockerfile = repo + "/" + service_name(service), "infra/docker/Dockerfile"
        tag = name + ":" + sha
        run(["docker", "build", "--platform=linux/amd64", "--build-arg=COMPONENT="+service,
             "--build-arg=VCS_REF="+sha, "--build-arg=BUILD_CREATED="+created, "-f", dockerfile, "-t", tag,
             "https://github.com/escossio/ita-agent-batalha.git#"+sha])
        run(["docker", "push", tag])
        details = json.loads(run(["docker", "image", "inspect", tag]))[0]
        digest = next(d for d in details["RepoDigests"] if d.startswith(name+"@sha256:"))
        records.append(dict(service=service, sha=sha, image=name, tag=tag, digest=digest, dockerfile=dockerfile,
                            created=created, pushed_at=datetime.now(timezone.utc).isoformat()))
        path.write_text(json.dumps({"sha": sha, "images": records}, indent=2)+"\n")
    print("PREPARADO immutable image manifest: " + str(path))


def images(cfg):
    manifest = json.loads(artifact_path().read_text())
    sha = required("ITA_CERTIFIED_SHA", r"[0-9a-f]{40}")
    repo = repository(cfg)
    if manifest["sha"] != sha or len(manifest["images"]) != len(PLAN):
        raise ValueError("incomplete/mismatched image manifest")
    result = {}
    for item in manifest["images"]:
        service = item["service"]
        if (service not in PLAN or service in result or item["sha"] != sha
                or not re.fullmatch(re.escape(repo+"/"+service_name(service))+r"@sha256:[0-9a-f]{64}", item["digest"])):
            raise ValueError("invalid image manifest")
        result[service] = item["digest"]
    return sha, result


def describe(cfg, service):
    return json.loads(gc(cfg, "run", "services", "describe", service_name(service), "--region="+cfg["region"], "--format=json"))


def owned(detail):
    ns.name("service", detail["metadata"]["name"])
    ns.labels(detail["metadata"].get("labels", {}))


def environment(cfg, service, urls, bootstrap):
    env = dict(ITA_PLATFORM="cloudrun", ITA_RUNTIME_MODE="competition", ITA_CLOUD_BOOTSTRAP="1" if bootstrap else "0")
    if urls:
        needed = set(PLAN[service]["callees"]) | {service}
        if service == "api":
            needed.add("policy")  # signature audience only, no API -> Policy invocation
        for destination in needed:
            env["ITA_"+destination.upper().replace("-", "_")+"_URL"] = urls[destination]
    env["ITA_ALLOWED_CALLERS"] = ",".join(account(cfg, caller) for caller, spec in PLAN.items() if service in spec["callees"])
    if service in {"api", "policy"}:
        env["ITA_IDENTITY_SIGNER"] = account(cfg, "api")
    if service in {"api", "policy", "data"}:
        env["ITA_IDENTITY_REGISTRY_FILE"] = "/secrets/identity/registry.json"
    if service == "agent":
        env.update(ITA_MODEL_PROVIDER="vertex", GOOGLE_CLOUD_PROJECT=cfg["project"], GOOGLE_CLOUD_LOCATION=cfg["region"],
                   ITA_VERTEX_MODEL=required("ITA_VERTEX_MODEL", r"[A-Za-z0-9_.-]+"))
    if service == "data":
        dataset, table = table_config()
        env.update(ITA_DATA_PROVIDER="bigquery", GOOGLE_CLOUD_PROJECT=cfg["project"], ITA_BIGQUERY_DATASET=dataset,
                   ITA_BIGQUERY_TABLE=table, ITA_BIGQUERY_LOCATION=cfg["region"],
                   ITA_BIGQUERY_CURRENCY=required("ITA_BIGQUERY_CURRENCY", "BRL"),
                   ITA_BIGQUERY_MONEY_UNIT=required("ITA_BIGQUERY_MONEY_UNIT", "major"),
                   ITA_BIGQUERY_MAX_BYTES_BILLED=required("ITA_BIGQUERY_MAX_BYTES_BILLED", r"[1-9][0-9]{0,12}"))
    return env


def deploy(cfg, phase):
    ns.scope(cfg)
    sha, digests = images(cfg)
    bootstrap = phase == "bootstrap"
    urls = {}
    if bootstrap:
        existing = json.loads(gc(cfg, "run", "services", "list", "--region="+cfg["region"], "--format=json"))
        if any(s["metadata"]["name"] in {service_name(n) for n in PLAN} for s in existing):
            blocked("bootstrap", prefix(), "service already exists", "Inspect partial run; perform reviewed cleanup of owned resources. Never overwrite live services.")
    else:
        for service in PLAN:
            detail = describe(cfg, service)
            owned(detail)
            urls[service] = detail["status"]["url"]
        # Reject stale broad invoker grants instead of silently removing others' IAM.
        for service in PLAN:
            policy = json.loads(gc(cfg, "run", "services", "get-iam-policy", service_name(service), "--region="+cfg["region"], "--format=json"))
            expected = {"serviceAccount:"+account(cfg, caller) for caller, spec in PLAN.items() if service in spec["callees"]}
            for binding in policy.get("bindings", []):
                if binding["role"] == "roles/run.invoker" and set(binding["members"]) - expected:
                    blocked("verify invokers", service_name(service), "unexpected invoker binding", "Review IAM explicitly before configuring the preview.")
    ingress = os.environ.get("ITA_CLOUD_RUN_INGRESS", "all")
    if ingress not in {"all", "internal", "internal-and-cloud-load-balancing"}:
        raise ValueError("invalid ingress")
    # Validate all configuration before the first deploy; no partial env edits.
    envs = {s: environment(cfg, s, urls, bootstrap) for s in PLAN}
    verify_runtime_resources(cfg)
    secret = ns.name("secret", required("ITA_IDENTITY_SECRET", r"[a-zA-Z0-9_-]{1,255}"))
    secret_version = required("ITA_IDENTITY_SECRET_VERSION", r"[1-9][0-9]*")
    if not bootstrap:
        for caller, spec in PLAN.items():
            for callee in spec["callees"]:
                gc(cfg, "run", "services", "add-iam-policy-binding", service_name(callee), "--region="+cfg["region"],
                   "--member=serviceAccount:"+account(cfg, caller), "--role=roles/run.invoker", "--condition=None")
    with tempfile.TemporaryDirectory() as temp:
        for service in PLAN:
            path = Path(temp) / (service+".json")
            path.write_text(json.dumps(envs[service]))
            args = ["run", "deploy", service_name(service), "--region="+cfg["region"], "--image="+digests[service],
                    "--service-account="+account(cfg, service), "--env-vars-file="+str(path), "--port=8080",
                    "--no-allow-unauthenticated", "--invoker-iam-check", "--ingress="+ingress,
                    "--execution-environment=gen2", "--memory=512Mi", "--cpu=1", "--concurrency=8", "--timeout=60",
                    "--min-instances=0", "--max-instances=2", "--startup-probe=httpGet.path=/healthz,httpGet.port=8080",
                    "--labels="+",".join(k+"="+v for k, v in ns.OWNER.items())+",ita-escossio-sha="+sha]
            if service in {"api", "policy", "data"}:
                args += ["--set-secrets=/secrets/identity/registry.json="+secret+":"+secret_version]
            gc(cfg, *args)
    print("PREPARADO phase " + phase + "; web still private. Publishing web requires a separate explicit action.")


def publish_web(cfg):
    owned(describe(cfg, "web"))
    gc(cfg, "run", "services", "add-iam-policy-binding", service_name("web"), "--region="+cfg["region"],
       "--member=allUsers", "--role=roles/run.invoker", "--condition=None")


def smoke(cfg):
    # Only operator-invoked real smoke. No financial rows/tokens printed.
    detail = describe(cfg, "web")
    owned(detail)
    url = detail["status"]["url"]
    session_file = Path(os.environ["ITA_SMOKE_SESSION_FILE"])
    if session_file.stat().st_mode & 0o077:
        raise ValueError("session file must be private (chmod 600)")
    session = session_file.read_text().strip()
    if not 32 <= len(session) <= 512:
        raise ValueError("invalid session")
    from uuid import uuid4
    cid = str(uuid4())
    payload = dict(utterance="Até o próximo salário dá?", amount_brl="0.00", demo_case="standard", consent_to_analysis=True,
                   window={"from_time": os.environ["ITA_SMOKE_FROM"], "to_time": os.environ["ITA_SMOKE_TO"]})
    request = urllib.request.Request(url+"/api/chat", data=json.dumps(payload).encode(), headers={
        "Content-Type": "application/json", "X-Correlation-ID": cid, "Authorization": "Bearer "+session})
    with urllib.request.urlopen(request, timeout=65) as response:
        value = json.load(response)
        assert response.headers["X-Correlation-ID"] == cid
    assert value["status"] == "needs_data" and value["financial_result"] is None
    context = value["financial_context"]
    assert context["status"] == "INCOMPLETE_FINANCIAL_CONTEXT"
    assert context["observed"]["provenance"] == "COMPETITION_SYNTHETIC_BIGQUERY"
    assert not context["estimates"] and not context["inferences"]
    # No consent must stay denied; do not print either response's financial payload.
    payload["consent_to_analysis"] = False
    request = urllib.request.Request(url+"/api/chat", data=json.dumps(payload).encode(), headers={
        "Content-Type": "application/json", "Authorization": "Bearer "+session})
    with urllib.request.urlopen(request, timeout=65) as response:
        assert json.load(response)["status"] == "denied"
    for service in PLAN:
        if service == "web":
            continue
        internal_url = describe(cfg, service)["status"]["url"]
        try:
            urllib.request.urlopen(internal_url+"/healthz", timeout=15)
        except urllib.error.HTTPError as error:
            assert error.code in {401, 403}
        else:
            raise AssertionError("anonymous internal invocation accepted")
    print(json.dumps(dict(status="PASS", correlation_id=cid, result="INCOMPLETE_FINANCIAL_CONTEXT", anonymous_internal="DENIED")))


def destroy(cfg, confirmation):
    if confirmation != prefix():
        raise ValueError("explicit preview name confirmation required")
    for service in PLAN:
        owned(describe(cfg, service))
    for service in PLAN:
        gc(cfg, "run", "services", "delete", service_name(service), "--region="+cfg["region"])
    print("Only owned namespace services removed. SAs/secrets/images preserved for separate review.")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("operation", choices=["preflight", "artifact_repository", "identities", "build_push", "deploy", "publish_web", "smoke", "destroy_preview"])
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--phase", choices=["bootstrap", "configure"])
    parser.add_argument("--confirm-preview")
    args = parser.parse_args()
    if not os.getenv("DEVSHELL_PROJECT_ID"):
        blocked("execution", "host", "Cloud Shell environment required", "Clone and run in Google Cloud Shell; never run gcloud on AGT.")
    tools = ("gcloud",) if args.operation == "artifact_repository" else ("gcloud", "docker", "bq", "git")
    for tool in tools:
        if not shutil.which(tool):
            blocked("tool availability", tool, "missing", "Use a Cloud Shell with the required tools.")
    cfg = config()
    if args.operation not in {"preflight", "smoke"} and not args.apply:
        blocked("mutation gate", args.operation, "--apply absent", "Run read-only preflight and obtain authorization before explicitly applying.")
    if args.operation == "preflight":
        preflight(cfg)
    elif args.operation == "artifact_repository":
        print(repository(cfg, create=True))
    elif args.operation == "identities":
        identities(cfg)
    elif args.operation == "build_push":
        build_push(cfg)
    elif args.operation == "deploy":
        if not args.phase:
            raise ValueError("explicit --phase required")
        deploy(cfg, args.phase)
    elif args.operation == "publish_web":
        publish_web(cfg)
    elif args.operation == "smoke":
        smoke(cfg)
    elif args.operation == "destroy_preview":
        destroy(cfg, args.confirm_preview)


if __name__ == "__main__":
    try:
        main()
    except Blocked as error:
        print(error, file=sys.stderr)
        sys.exit(2)
    except Exception as error:
        # No payload/token traceback from remote services. Gcloud errors handled above.
        print(f"BLOCKED\noperation: operator tooling\nresource: configured target\nerror: {type(error).__name__}\nnext human action: inspect configuration and permissions locally", file=sys.stderr)
        sys.exit(2)
