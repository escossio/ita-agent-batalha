"""Restrições de dependência aplicadas ao código de runtime existente."""

import ast
import json
from pathlib import Path
import subprocess
from urllib.parse import urlsplit


def violations(path: Path, source: str) -> list[str]:
    issues = []
    tree = ast.parse(source)
    is_agent = "agent" in path.parts
    is_vertex_owner = path.parts[:2] == ("services", "agent")
    is_data = path.parts[:2] == ("services", "data")
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names = [n.name for n in node.names]
        elif isinstance(node, ast.ImportFrom):
            names = [node.module or ""] + [f"{node.module or ''}.{alias.name}" for alias in node.names]
        else:
            names = []
        for name in names:
            if not is_vertex_owner and any(part in name.split(".") for part in ("vertexai", "aiplatform", "genai")):
                issues.append(f"{path}:{node.lineno}: Vertex is exclusive to Agent")
            if not is_data and any(part in name.split(".") for part in ("bigquery", "bigquery_storage")):
                issues.append(f"{path}:{node.lineno}: BigQuery is exclusive to Data Access")
            if is_agent and any(part in name.split(".") for part in (
                "psycopg", "psycopg2", "sqlalchemy", "sqlite3", "subprocess",
                "finance", "data", "policy", "broker", "bigquery", "bigquery_storage",
            )):
                issues.append(f"{path}:{node.lineno}: forbidden agent import {name}")
        if not is_data and isinstance(node, ast.Constant) and isinstance(node.value, str):
            try:
                host = urlsplit(node.value).hostname if node.value.startswith(("http://", "https://")) else node.value
            except ValueError:
                host = None
            if host in {"bigquery.googleapis.com", "bigquerystorage.googleapis.com"}:
                issues.append(f"{path}:{node.lineno}: BigQuery endpoint outside Data Access forbidden")
        if not is_vertex_owner and isinstance(node, ast.Constant) and isinstance(node.value, str):
            try:
                vertex_host = urlsplit(node.value if node.value.startswith(("http://", "https://")) else "//" + node.value).hostname
            except ValueError:
                vertex_host = None
            if vertex_host and (vertex_host == "aiplatform.googleapis.com" or vertex_host.endswith("-aiplatform.googleapis.com")):
                issues.append(f"{path}:{node.lineno}: Vertex endpoint outside Agent forbidden")
        if is_agent and isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            if node.func.id in {"eval", "exec", "__import__"}:
                issues.append(f"{path}:{node.lineno}: dynamic execution forbidden")
    return issues


def network_violations(config: dict) -> list[str]:
    issues = []
    services = config["services"]
    for name, spec in services.items():
        if spec.get("privileged") or spec.get("network_mode") == "host":
            issues.append(f"{name}: host privilege/network forbidden")
        if name != "web" and spec.get("ports"):
            issues.append(f"{name}: internal service port exposed")
        for mount in spec.get("volumes", []):
            if "docker.sock" in str(mount):
                issues.append(f"{name}: Docker socket forbidden")
    for left, right in (("agent", "postgres"), ("agent", "finance"), ("agent", "data"),
                        ("api", "postgres"), ("web", "postgres"), ("tool-broker", "postgres")):
        if set(services[left].get("networks", {})) & set(services[right].get("networks", {})):
            issues.append(f"forbidden shared network: {left}/{right}")
    if services["agent"].get("volumes"):
        issues.append("agent: secret/data volumes forbidden")
    if any("DB_" in name or "POSTGRES" in name for name in services["agent"].get("environment", {})):
        issues.append("agent: database configuration forbidden")
    for name, spec in services.items():
        if name != "data" and any(key.startswith("ITA_BIGQUERY_") for key in spec.get("environment", {})):
            issues.append(f"{name}: BigQuery configuration outside Data Access")
    for name, network in config["networks"].items():
        if name not in {"edge", "model_egress", "data_egress"} and not network.get("internal"):
            issues.append(f"{name}: network must be internal")
    if "data_egress" in config["networks"]:
        attached = {name for name, spec in services.items() if "data_egress" in spec.get("networks", {})}
        if attached != {"data"}:
            issues.append("data_egress: only Data Access may reach BigQuery")
    if "model_egress" in config["networks"]:
        attached = {name for name, spec in services.items() if "model_egress" in spec.get("networks", {})}
        if attached != {"agent"}:
            issues.append("model_egress: only agent may use provider egress")
    return issues


if __name__ == "__main__":
    problems = []
    count = 0
    for root in ("apps", "services", "packages"):
        for path in Path(root).rglob("*.py"):
            count += 1
            problems.extend(violations(path, path.read_text()))
    config = json.loads(subprocess.check_output(["docker", "compose", "config", "--format", "json"]))
    problems.extend(network_violations(config))
    from cloudrun_check import check as cloudrun_check
    problems.extend(cloudrun_check())
    for problem in problems:
        print(problem)
    print(f"architecture: {count} runtime files checked; {len(problems)} violations")
    raise SystemExit(bool(problems))
