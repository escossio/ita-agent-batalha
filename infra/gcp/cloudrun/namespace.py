"""Fail-closed operator boundary. Shared project/data are read-only targets."""
import json
import os
from pathlib import Path
import re

PROJECT = "batalha-time-01-97zr"
REGION = "us-central1"
PREFIX = "ita-escossio"
OWNER = {"ita-escossio-owner": PREFIX, "ita-escossio-managed": "ita-agent-batalha"}
SA_DESCRIPTION = "ita-escossio-managed:ita-agent-batalha"
SUFFIXES = {"web", "api", "agent", "policy", "broker", "data", "finance"}
EDGES = {"web": {"api"}, "api": {"agent"}, "agent": {"policy", "broker"},
         "broker": {"policy", "data", "finance"}, "data": {"policy"}, "policy": set(), "finance": set()}


class Blocked(Exception):
    pass


def blocked(operation, resource, error, action):
    raise Blocked(f"BLOCKED\noperation: {operation}\nresource: {resource}\nerror: {error}\nnext human action: {action}")


def deny(resource, reason="outside authorized namespace/operation"):
    blocked("namespace guard", resource, reason, "Stop; request explicit human review. No shared-resource fallback.")


def prefix():
    if os.getenv("ITA_CLOUD_RUN_PREFIX"):
        deny("ITA_CLOUD_RUN_PREFIX", "obsolete preview override; use ITA_RESOURCE_PREFIX")
    if os.getenv("ITA_RESOURCE_PREFIX", PREFIX) != PREFIX:
        deny("ITA_RESOURCE_PREFIX", "only ita-escossio is authorized")
    return PREFIX


def scope(cfg):
    prefix()
    if cfg != dict(project=PROJECT, region=REGION):
        deny("project/region", "target differs from operator-confirmed project/region")


def name(kind, value):
    if kind not in {"repository", "account", "secret", "service", "package"}:
        deny(kind, "unknown resource kind")
    p = prefix()
    allowed = {p+"-"+s for s in SUFFIXES}
    if kind == "repository":
        allowed = {p}
    elif kind == "account":
        allowed = {p+"-"+s+"-sa" for s in SUFFIXES}
    elif kind == "secret":
        allowed = {p+"-identity-registry"}
    if value not in allowed:
        deny(value)
    return value


def account(value):
    local, separator, domain = value.partition("@")
    if separator != "@" or domain != PROJECT+".iam.gserviceaccount.com":
        deny(value)
    return name("account", local)


def image(value, digest=False):
    base = REGION+"-docker.pkg.dev/"+PROJECT+"/"+PREFIX+"/"
    separator = "@sha256:" if digest else ":"
    path, sep, version = value.partition(separator)
    if not path.startswith(base) or sep != separator or not re.fullmatch(r"[0-9a-f]{64}" if digest else r"[0-9a-f]{40}", version):
        deny(value, "only our repository/package and immutable digest or full Git SHA allowed")
    name("package", path.removeprefix(base))


def labels(values):
    if any(values.get(k) != v for k, v in OWNER.items()):
        deny("ownership labels", "existing resource is not owned; never adopt/relabel")


def command(args):
    """Called immediately before every subprocess. Unknown GCP operations deny."""
    prefix()
    if args[0] == "docker":
        if args[1] == "push":
            if len(args) != 3:
                deny("docker push arguments")
            image(args[2])
        elif args[1] == "build":
            image(args[args.index("-t")+1])
        elif args[1:3] != ["image", "inspect"] and args[1] != "version":
            deny("docker operation")
        return
    if args[0] == "git":
        if args[1] not in {"rev-parse", "status", "show"}:
            deny("git operation")
        return
    if args[0] == "bq":
        source = PROJECT+":hackathon_dados.extrato_sintetico"
        query = f"SELECT id_usuario, vlr, saldo_apos FROM `{PROJECT}.hackathon_dados.extrato_sintetico` WHERE FALSE"
        if args not in (["bq", "--project_id="+PROJECT, "show", "--format=prettyjson", source],
                        ["bq", "--project_id="+PROJECT, "query", "--location="+REGION, "--use_legacy_sql=false", "--dry_run", query]):
            deny("BigQuery operation", "only metadata and the reviewed dry-run are permitted")
        return
    if args[0] != "gcloud":
        deny(args[0], "unreviewed executable")
    words = tuple(a for a in args[1:] if not a.startswith("--"))
    flags = {}
    for arg in args[1:]:
        if arg.startswith("--"):
            key, _, value = arg.partition("=")
            if key in flags:
                deny(key, "duplicate flag")
            flags[key] = value
    readonly = {("config", "get-value", "project"), ("auth", "list"), ("services", "list"),
                ("ai", "models", "list"), ("artifacts", "repositories", "list"),
                ("run", "services", "list"), ("iam", "service-accounts", "list")}
    if words in readonly:
        return
    for start in (("run", "services", "describe"), ("run", "services", "get-iam-policy"),
                  ("iam", "service-accounts", "describe"), ("secrets", "describe")):
        if words[:len(start)] == start and len(words) == len(start)+1:
            return
    scope(dict(project=flags.get("--project"), region=flags.get("--region", flags.get("--location", REGION))))
    allowed_flags = {"--project", "--quiet"}
    if words[:3] == ("artifacts", "repositories", "create") and len(words) == 4:
        name("repository", words[3])
        allowed_flags |= {"--location", "--repository-format", "--labels", "--immutable-tags"}
        if flags.get("--repository-format") != "docker" or "--immutable-tags" not in flags or flags.get("--location") != REGION:
            deny("repository format/location/tag policy")
        labels(dict(item.split("=", 1) for item in flags.get("--labels", "").split(",") if "=" in item))
    elif words[:3] == ("iam", "service-accounts", "create") and len(words) == 4:
        name("account", words[3])
        allowed_flags |= {"--description"}
        if flags.get("--description") != SA_DESCRIPTION:
            deny("service account ownership marker")
    elif words[:2] == ("auth", "configure-docker") and words[2:] == (REGION+"-docker.pkg.dev",):
        pass  # local Docker credential helper configuration; no IAM/resource mutation
    elif words[:2] == ("run", "deploy") and len(words) == 3:
        service = name("service", words[2])
        account(flags.get("--service-account", ""))
        if flags["--service-account"].split("@")[0] != service+"-sa":
            deny(service, "service/account mismatch")
        image(flags.get("--image", ""), digest=True)
        if "/"+service+"@sha256:" not in flags["--image"]:
            deny(service, "service/image mismatch")
        allowed_flags |= {"--region", "--image", "--service-account", "--env-vars-file", "--port",
                          "--no-allow-unauthenticated", "--invoker-iam-check", "--ingress", "--execution-environment",
                          "--memory", "--cpu", "--concurrency", "--timeout", "--min-instances", "--max-instances",
                          "--startup-probe", "--labels", "--set-secrets"}
        if not {"--no-allow-unauthenticated", "--invoker-iam-check"} <= flags.keys():
            deny(service, "IAM checks required")
        labels(dict(item.split("=", 1) for item in flags.get("--labels", "").split(",") if "=" in item))
        env = json.loads(Path(flags["--env-vars-file"]).read_text())
        if any("CREDENTIAL" in k or k.startswith("DB_") for k in env):
            deny(service, "credential files/database environment forbidden")
        mount = flags.get("--set-secrets")
        if mount and (service not in {PREFIX+"-"+s for s in ("api", "policy", "data")} or not re.fullmatch(
                r"/secrets/identity/registry.json="+PREFIX+r"-identity-registry:[1-9][0-9]*", mount)):
            deny(service, "unreviewed secret mount")
    elif words[:3] in {("run", "services", "add-iam-policy-binding"), ("run", "services", "delete")} and len(words) == 4:
        target = name("service", words[3])
        allowed_flags |= {"--region"}
        if words[2] == "add-iam-policy-binding":
            allowed_flags |= {"--member", "--role", "--condition"}
            member = flags.get("--member", "")
            if member == "allUsers":
                if target != PREFIX+"-web":
                    deny(target, "only Web is a public candidate")
            else:
                if not member.startswith("serviceAccount:"):
                    deny(member)
                caller = account(member.removeprefix("serviceAccount:")).removeprefix(PREFIX+"-").removesuffix("-sa")
                if target.removeprefix(PREFIX+"-") not in EDGES[caller]:
                    deny(target, "unreviewed caller/callee")
            if flags.get("--role") != "roles/run.invoker" or flags.get("--condition") != "None":
                deny(target, "unreviewed IAM role/condition")
    else:
        deny(" ".join(words), "mutation not allow-listed; project/table IAM is explicitly read-only")
    if flags.keys() - allowed_flags:
        deny(",".join(sorted(flags.keys()-allowed_flags)), "unreviewed mutation flags")
