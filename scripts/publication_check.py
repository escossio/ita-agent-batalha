"""Revisa árvore rastreada e expande XLSX para varredura; nunca imprime achados brutos."""

import argparse
import hashlib
import io
import ipaddress
import json
from pathlib import Path
import re
import subprocess
import zipfile


def inspect(name: str, data: bytes) -> list[str]:
    findings = []
    text = data.decode("utf-8")
    if re.search(r"\b\d{3}\.\d{3}\.\d{3}-\d{2}\b", text):
        findings.append(f"{name}: potential personal identifier")
    for email in re.findall(r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}", text):
        if not email.endswith("@users.noreply.github.com"):
            findings.append(f"{name}: personal email")
    for value in re.findall(r"(?<![\w.])(?:\d{1,3}\.){3}\d{1,3}(?![\w.])", text):
        try:
            address = ipaddress.ip_address(value)
            if address.is_private and not (address.is_loopback or address.is_unspecified):
                findings.append(f"{name}: private network address")
        except ValueError:
            pass
    return findings


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--expand-to", type=Path, required=True)
    args = parser.parse_args()
    args.expand_to.mkdir(parents=True, exist_ok=True)
    findings = []
    names = subprocess.check_output(["git", "ls-files", "-z"]).decode().split("\0")
    for name in filter(None, names):
        path = Path(name)
        if path.name == ".env" or path.suffix in {".dump", ".pem", ".key", ".p12", ".pfx"}:
            findings.append(f"{name}: forbidden file")
        data = path.read_bytes()
        if path.suffix == ".xlsx":
            with zipfile.ZipFile(io.BytesIO(data)) as archive:
                if archive.testzip() is not None:
                    findings.append(f"{name}: invalid ZIP")
                for item in archive.infolist():
                    payload = archive.read(item)
                    findings.extend(inspect(name + ":" + item.filename, payload))
                    target = args.expand_to / (hashlib.sha256((name + item.filename).encode()).hexdigest() + ".xml")
                    target.write_bytes(payload)
        else:
            findings.extend(inspect(name, data))
    manifest = json.loads(Path("docs/source/manifest.json").read_text())
    for source in manifest["sources"]:
        if source["status"] == "SOURCE_PENDING_LOCAL_COPY":
            assert source["path"] is None and source["sha256"] is None
            continue
        assert hashlib.sha256(Path(source["path"]).read_bytes()).hexdigest() == source["sha256"]
    for finding in findings:
        print(finding)
    print(f"publication: {len(findings)} findings; local source hashes verified")
    raise SystemExit(bool(findings))
