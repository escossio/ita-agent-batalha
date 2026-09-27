"""Cloud target guard; operates on source/config without gcloud or credentials."""
import ast
import json
from pathlib import Path

EDGES = {"web": {"api"}, "api": {"agent"}, "agent": {"policy", "tool-broker"}, "policy": set(),
         "tool-broker": {"policy", "data", "finance"}, "data": {"policy"}, "finance": set()}


def plan_violations(plan):
    problems = []
    if set(plan) != set(EDGES):
        problems.append("Cloud Run: physical services differ from reviewed seven-service plan")
    for name, spec in plan.items():
        suffix = "broker" if name == "tool-broker" else name
        if spec.get("resource_suffix") != suffix or spec.get("service_account") != "ita-escossio-"+suffix+"-sa":
            problems.append("Cloud Run: service/account outside authorized namespace")
        if set(spec.get("callees", [])) != EDGES.get(name, set()):
            problems.append("Cloud Run: unauthorized caller/callee edge: " + name)
        if spec.get("public_candidate") != (name == "web"):
            problems.append("Cloud Run: only Web may be public")
    if len({s.get("service_account") for s in plan.values()}) != len(plan):
        problems.append("Cloud Run: distinct service identities required")
    return problems


def check():
    problems = plan_violations(json.loads(Path("infra/gcp/cloudrun/services.json").read_text()))
    for path in Path("infra/gcp/cloudrun").glob("*.sh"):
        if "set -euo pipefail" not in path.read_text():
            problems.append(f"{path}: strict shell required")
    operator = Path("infra/gcp/cloudrun/operator.py").read_text()
    for forbidden in ("--allow-unauthenticated", "--no-invoker-iam-check", "--vpc-connector", "--set-cloudsql-instances",
                      "sqladmin.googleapis.com", "vpcaccess.googleapis.com", "roles/owner", "roles/editor", "keys", "latest"):
        # inspect complete command arguments, not comments/variable names
        if any(isinstance(n, ast.Constant) and n.value == forbidden for n in ast.walk(ast.parse(operator))):
            problems.append("Cloud Run: forbidden deployment argument " + forbidden)
    if '"--no-allow-unauthenticated"' not in operator or '"--invoker-iam-check"' not in operator:
        problems.append("Cloud Run: IAM invocation gate missing")
    run_node = next(n for n in ast.parse(operator).body if isinstance(n, ast.FunctionDef) and n.name == "run")
    if ast.unparse(run_node.body[0]) != "ns.command(args)":
        problems.append("Cloud Run: namespace guard must run before subprocess")
    for path in Path("infra/gcp/cloudrun").glob("*.py"):
        for node in ast.walk(ast.parse(path.read_text())):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and isinstance(node.func.value, ast.Name):
                if node.func.value.id == "subprocess" and (path.name != "operator.py" or node.func.attr != "run"):
                    problems.append("Cloud Run: unguarded subprocess boundary")
    for path in Path("infra/gcp/cloudrun").glob("*.sh"):
        if path.read_text().splitlines()[2:3] != ['exec python3 "$(dirname "$0")/operator.py" '+path.stem+' "$@"']:
            problems.append("Cloud Run: shell must delegate exclusively to guarded operator")
    server = ast.parse(Path("packages/runtime/server.py").read_text())
    for node in ast.walk(server):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "ThreadingHTTPServer":
            bind = node.args[0]
            if not isinstance(bind, ast.Tuple) or not isinstance(bind.elts[1], ast.Call) or bind.elts[1].func.id != "listen_port":
                problems.append("Cloud Run: fixed port forbidden")
    for root in (Path("services"), Path("packages"), Path("infra/gcp/cloudrun")):
        for path in root.rglob("*.json"):
            value = json.loads(path.read_text())
            if isinstance(value, dict) and (value.get("type") == "service_account" or "private_key" in value):
                problems.append(f"{path}: credential JSON forbidden")
    return problems
