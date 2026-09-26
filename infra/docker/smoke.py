"""Smoke da fundação e prova de isolamento; executar somente em worker."""

import json
import subprocess
import urllib.request
from uuid import uuid4


def compose(*args):
    return subprocess.check_output(["docker", "compose", *args], text=True).strip()


if __name__ == "__main__":
    address = compose("port", "web", "8080")
    cid = str(uuid4())
    request = urllib.request.Request(f"http://{address}/healthz", headers={"X-Correlation-ID": cid})
    with urllib.request.urlopen(request, timeout=5) as response:
        assert response.headers["X-Correlation-ID"] == cid
        assert json.load(response)["service"] == "web"
    services = ("web", "api", "agent", "policy", "tool-broker", "finance", "data", "observability")
    for service in services:
        compose("exec", "-T", service, "python", "-c",
                "import urllib.request; urllib.request.urlopen('http://localhost:8080/healthz',timeout=3)")
    # Probe actual container IPs as well as DNS, so lack of discovery alone is not proof.
    for target, port in (("postgres", 5432), ("finance", 8080), ("data", 8080)):
        info = json.loads(subprocess.check_output(["docker", "inspect", compose("ps", "-q", target)]))[0]
        addresses = [n["IPAddress"] for n in info["NetworkSettings"]["Networks"].values()]
        code = (
            "import socket,sys\n"
            "for host in sys.argv[1:]:\n"
            " try:\n"
            f"  conn=socket.create_connection((host,{port}),timeout=0.6)\n"
            " except OSError: continue\n"
            " else: conn.close(); raise SystemExit('BYPASS REACHABLE')\n"
        )
        compose("exec", "-T", "agent", "python", "-c", code, target, *addresses)
    compose("exec", "-T", "agent", "python", "-c",
            "from pathlib import Path; assert not Path('/run/secrets/db-password').exists(); "
            "assert not Path('/app/component/../finance').exists()")
    compose("stop", "--timeout", "10")
    for service in services:
        info = json.loads(subprocess.check_output(["docker", "inspect", compose("ps", "-aq", service)]))[0]
        assert info["State"]["ExitCode"] == 0, service
        assert "shutdown.completed" in compose("logs", "--no-color", service), service
    print("PASS: health, correlation ID, direct-IP/DNS bypass denied, secret isolation, clean shutdown")
