"""Restrições de dependência aplicadas ao código de runtime existente."""

import ast
from pathlib import Path


def violations(path: Path, source: str) -> list[str]:
    issues = []
    tree = ast.parse(source)
    is_agent = "agent" in path.parts
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names = [n.name for n in node.names]
        elif isinstance(node, ast.ImportFrom):
            names = [node.module or ""]
        else:
            names = []
        for name in names:
            if is_agent and any(part in name.split(".") for part in (
                "psycopg", "psycopg2", "sqlalchemy", "sqlite3", "subprocess",
                "finance", "data", "policy", "broker",
            )):
                issues.append(f"{path}:{node.lineno}: forbidden agent import {name}")
        if is_agent and isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            if node.func.id in {"eval", "exec", "__import__"}:
                issues.append(f"{path}:{node.lineno}: dynamic execution forbidden")
    return issues


if __name__ == "__main__":
    problems = []
    count = 0
    for root in ("apps", "services", "packages"):
        for path in Path(root).rglob("*.py"):
            count += 1
            problems.extend(violations(path, path.read_text()))
    for problem in problems:
        print(problem)
    print(f"architecture: {count} runtime files checked; {len(problems)} violations")
    raise SystemExit(bool(problems))
