"""Worker-only, same images, dynamic port/read-only FS/no network or volumes."""
import json
import os
import subprocess
import time
from uuid import uuid4

assert os.environ.get("ITA_CI_WORKER") == "1", "worker required"
project = os.environ["COMPOSE_PROJECT_NAME"]
services = ("web", "api", "agent", "policy", "tool-broker", "data", "finance", "observability")
for service in services:
    name = "ita-ready-" + uuid4().hex[:12]
    env = dict(PORT="9091", ITA_PLATFORM="cloudrun", ITA_CLOUD_BOOTSTRAP="1", ITA_RUNTIME_MODE="competition",
               ITA_DATA_PROVIDER="bigquery", GOOGLE_CLOUD_PROJECT="example-project", ITA_BIGQUERY_DATASET="demo",
               ITA_BIGQUERY_TABLE="ledger", ITA_BIGQUERY_LOCATION="us-central1", ITA_BIGQUERY_CURRENCY="BRL",
               ITA_BIGQUERY_MONEY_UNIT="major", ITA_BIGQUERY_MAX_BYTES_BILLED="1000000")
    args = ["docker", "run", "-d", "--name", name, "--read-only", "--network=none", "--cap-drop=ALL",
            "--security-opt=no-new-privileges", "--memory=256m", "--cpus=0.5"]
    for key, value in env.items():
        args += ["-e", key+"="+value]
    args += [project+"-"+service]
    try:
        subprocess.run(args, check=True, capture_output=True)
        probe = "import json, urllib.request; import google.auth; r=urllib.request.urlopen('http://127.0.0.1:9091/healthz',timeout=2); assert r.status==200"
        for _ in range(30):
            result = subprocess.run(["docker", "exec", name, "python", "-c", probe], capture_output=True)
            if result.returncode == 0:
                break
            time.sleep(0.3)
        else:
            raise AssertionError("dynamic port/startup failed: " + service)
        subprocess.run(["docker", "stop", "--time=8", name], check=True, capture_output=True)
        state = json.loads(subprocess.check_output(["docker", "inspect", name]))[0]
        assert state["State"]["ExitCode"] == 0 and not state["Mounts"], service
        logs = subprocess.check_output(["docker", "logs", name], stderr=subprocess.STDOUT).decode()
        assert '"event": "shutdown.completed"' in logs, service
        assert '"event": "startup.ready"' in logs, service
    finally:
        subprocess.run(["docker", "rm", "-f", name], capture_output=True, check=False)
print("PASS: 8 HTTP images, dynamic PORT, no network/volumes, read-only filesystem, ADC library, startup/SIGTERM")
