"""Transformação determinística das fontes congeladas; nunca usada no runtime."""

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import posixpath
import re
import xml.etree.ElementTree as ET
import zipfile

NS = {"s": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
REL = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id"


def workbook(path: Path) -> dict:
    """Keep exact cell text and coordinates, including empty cells."""
    sheets = {}
    with zipfile.ZipFile(path) as archive:
        if archive.testzip() is not None:
            raise ValueError("invalid source archive")
        shared = ["".join(cell.itertext()) for cell in ET.fromstring(archive.read("xl/sharedStrings.xml"))]
        relationships = {item.attrib["Id"]: item.attrib["Target"]
                         for item in ET.fromstring(archive.read("xl/_rels/workbook.xml.rels"))}
        book = ET.fromstring(archive.read("xl/workbook.xml"))
        for sheet in book.findall("s:sheets/s:sheet", NS):
            target = relationships[sheet.attrib[REL]]
            target = target.lstrip("/") if target.startswith("/") else posixpath.normpath("xl/" + target)
            if not target.startswith("xl/worksheets/"):
                raise ValueError("unsupported worksheet relationship")
            rows = []
            for row in ET.fromstring(archive.read(target)).findall("s:sheetData/s:row", NS):
                cells = {}
                for cell in row.findall("s:c", NS):
                    if cell.find("s:f", NS) is not None:
                        raise ValueError("formula source requires explicit review")
                    value = cell.find("s:v", NS)
                    inline = cell.find("s:is", NS)
                    text = value.text or "" if value is not None else "".join(inline.itertext()) if inline is not None else ""
                    if cell.attrib.get("t") == "s":
                        text = shared[int(text)]
                    cells[cell.attrib["r"]] = text
                rows.append({"row": int(row.attrib["r"]), "cells": cells})
            sheets[sheet.attrib["name"]] = rows
    return sheets


def cell(row: dict, column: str) -> str:
    return row["cells"].get(column + str(row["row"]), "")


def conditions(text: str) -> list[dict]:
    result = []
    for term in text.split(" AND "):
        match = re.fullmatch(r"([a-z_]+)\s*=\s*([^=]+)", term)
        if not match:
            raise ValueError(f"unsupported rule expression: {text}")
        value = match.group(2).strip()
        result.append({"field": match.group(1), "operator": "eq", "value": {"SIM": True, "NÃO": False}.get(value, value)})
    return result


def rendered(value) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n"


def derive() -> dict[str, str]:
    manifest = json.loads(Path("docs/source/manifest.json").read_text())
    sources = {item["id"]: item for item in manifest["sources"]}
    tables = {}
    for key in ("decision_rules", "evaluation_scenarios"):
        source = sources[key]
        path = Path(source["path"])
        if hashlib.sha256(path.read_bytes()).hexdigest() != source["sha256"]:
            raise ValueError("source hash mismatch: " + key)
        tables[key] = workbook(path)
    source = sources["decision_rules"]
    rule_rows = tables["decision_rules"]["Matriz_Regras"]
    rules = []
    for row in rule_rows[1:]:
        rules.append({
            "id": cell(row, "A"), "all": conditions(cell(row, "B")),
            "condition_text": cell(row, "B"), "candidate_solutions": cell(row, "C"),
            "priority_text": cell(row, "D"), "product_text": cell(row, "E"),
            "restriction_text": cell(row, "F"),
            "source": {"path": source["path"], "sha256": source["sha256"],
                       "sheet": "Matriz_Regras", "row": row["row"], "columns": "A:F"},
        })
    if [rule["id"] for rule in rules] != [f"R{i:03}" for i in range(1, 15)]:
        raise ValueError("rule IDs changed; explicit source review required")
    source = sources["evaluation_scenarios"]
    scenario_rows = tables["evaluation_scenarios"]["Cenarios_Treino"]
    scenarios = []
    for row in scenario_rows[1:]:
        record = dict(zip(("id", "interaction", "family", "utterance", "context", "expected_behavior"),
                          (cell(row, col) for col in "ABCDEF")))
        if not all(record.values()):
            raise ValueError("incomplete scenario row")
        record["source"] = {"path": source["path"], "sha256": source["sha256"],
                            "sheet": "Cenarios_Treino", "row": row["row"], "columns": "A:F"}
        scenarios.append(record)
    summary = tables["evaluation_scenarios"]["Resumo"]
    expected = {cell(row, "B"): int(cell(row, "C")) for row in summary[1:]}
    actual = dict(Counter(row["family"] for row in scenarios))
    ids = [row["id"] for row in scenarios]
    if len(scenarios) != 250 or len(set(ids)) != 250 or set(ids) != {f"CT-{i:03}" for i in range(1, 251)}:
        raise ValueError("expected exactly 250 unique original scenario IDs")
    if actual != expected or len(expected) != 5 or set(expected.values()) != {50}:
        raise ValueError("family totals do not match frozen source")
    if sources["voice_and_tone"]["status"] != "SOURCE_PENDING_LOCAL_COPY":
        raise ValueError("new Voice/Tone source requires explicit classification review")
    return {
        "config/rules.json": rendered({"schema_version": "1.0", "rules": rules}),
        "config/source_tables.json": rendered({"schema_version": "1.0", "tables": tables}),
        "config/voice/source_status.json": rendered({
            "schema_version": "1.0", "status": "SOURCE_PENDING_LOCAL_COPY", "blocking_structure": False,
            "generation_guidance": [], "behavior_rules": [], "safety_rules": [],
            "product_restrictions": [], "human_handoff": [], "definitive": False,
        }),
        "evals/scenarios.jsonl": "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in scenarios),
        "evals/expectations/source_behaviors.json": rendered({
            "schema_version": "1.0", "expectations": [
                {"scenario_id": row["id"], "behavior": row["expected_behavior"],
                 "source": row["source"], "runtime_assertions_status": "NOT_IMPLEMENTED"} for row in scenarios],
        }),
        "evals/integrity.json": rendered({"schema_version": "1.0", "total": 250, "unique_ids": 250,
                                           "families": actual, "expected_families": expected,
                                           "source_sha256": source["sha256"], "lost_scenarios": 0}),
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    for name, content in derive().items():
        path = Path(name)
        if args.check:
            if not path.exists() or path.read_text() != content:
                raise SystemExit("derived artifact drift: " + name)
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content)
    print("PASS: 14 rules; 250 unique scenarios; 5 families × 50; no source loss; Voice/Tone pending")
