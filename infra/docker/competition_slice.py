"""Full HTTP competition journey, synthetic BigQuery transport, worker only."""
from datetime import datetime, timedelta, timezone
import hashlib
import json
import os
from pathlib import Path
import secrets
import subprocess
import tempfile
import urllib.error
import urllib.request
from uuid import uuid4


def certify():
    if os.getenv("ITA_CI_WORKER") != "1":
        raise SystemExit("worker required")
    with tempfile.TemporaryDirectory(prefix="ita-competition-") as directory:
        root = Path(directory)
        root.chmod(0o755)
        session = secrets.token_urlsafe(48)
        registry = {"bindings": [{"context": dict(schema_version="1.0", customer_id="competition-client", mode="COMPETITION",
            provenance="VERIFIED_RUNTIME_IDENTITY", consent_to_analysis=True, financial_level="unknown", emotional_state="neutral", human_requested=False),
            "source_user_id": "synthetic-source-user", "session_hash": hashlib.sha256(session.encode()).hexdigest(),
            "expires_at": (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat(), "max_window_days": 366}]}
        (root / "registry.json").write_text(json.dumps(registry))
        row = dict(id_usuario="synthetic-source-user", anomesdia="1788307200", anomes="202609", tipo="UNVERIFIED_TYPE",
                   descr="Synthetic competition CI record", vlr="-12.345", saldo_apos="100.005", nom_cate_macro="synthetic macro",
                   nom_cate_micro=None, parcela_atual="2.0", parcela_total="3.0")
        (root / "rows.json").write_text(json.dumps([row]))
        override = {"services": {"data": {"environment": {"ITA_BIGQUERY_MOCK_ROWS_FILE": "/run/mock/rows.json"},
            "volumes": [{"type": "bind", "source": str(root / "rows.json"), "target": "/run/mock/rows.json", "read_only": True}]}}}
        # JSON is also YAML. Temporary paths and generated session material stay outside Git.
        (root / "mock.json").write_text(json.dumps(override))
        env = os.environ | dict(ITA_IDENTITY_REGISTRY_FILE=str(root / "registry.json"), ITA_DATA_PROVIDER="bigquery_mock",
            GOOGLE_CLOUD_PROJECT="demo-project", ITA_BIGQUERY_DATASET="demo_dataset", ITA_BIGQUERY_TABLE="demo_ledger",
            ITA_BIGQUERY_LOCATION="us-central1", ITA_BIGQUERY_CURRENCY="BRL", ITA_BIGQUERY_MONEY_UNIT="major",
            ITA_BIGQUERY_MAX_BYTES_BILLED="10000000")
        command = ["docker", "compose", "-f", "compose.yaml", "-f", "compose.bigquery.yaml", "-f", str(root / "mock.json")]

        def compose(*args):
            return subprocess.check_output(command + list(args), env=env, text=True).strip()

        def invoke(patch=None, authorized=True):
            payload = dict(utterance="Até o próximo salário dá?", amount_brl="500,00", consent_to_analysis=True,
                           window=dict(from_time="2026-09-01T00:00:00Z", to_time="2026-10-01T00:00:00Z"))
            payload.update(patch or {})
            cid = str(uuid4())
            headers = {"Content-Type": "application/json", "X-Correlation-ID": cid}
            if authorized:
                headers["Authorization"] = "Bearer " + session
            request = urllib.request.Request("http://" + compose("port", "web", "8080") + "/api/chat",
                                             data=json.dumps(payload).encode(), headers=headers)
            try:
                with urllib.request.urlopen(request, timeout=35) as response:
                    assert response.headers["X-Correlation-ID"] == cid
                    return response.status, json.load(response)
            except urllib.error.HTTPError as error:
                return error.code, json.load(error)

        try:
            compose("config", "--quiet")
            compose("up", "-d", "--no-build", "--pull", "never", "--wait", "--wait-timeout", "180")
            status, result = invoke()
            assert status == 200 and result["status"] == "needs_data", result
            context = result["financial_context"]
            assert context["status"] == "INCOMPLETE_FINANCIAL_CONTEXT"
            assert context["observed"]["provenance"] == "COMPETITION_SYNTHETIC_BIGQUERY_MOCK"
            assert context["observed"]["entries"][0]["amount_cents"] == -1235
            assert context["observed"]["entries"][0]["balance_after_cents"] == 10001
            assert context["observed"]["entries"][0]["installment_number"] == 2
            assert context["estimates"] == context["inferences"] == []
            assert result["financial_result"] is None
            assert invoke(authorized=False)[0] >= 400
            assert invoke({"customer_id": "other"})[0] >= 400
            assert invoke({"consent_to_analysis": False})[1]["status"] == "denied"
            (root / "rows.json").write_text(json.dumps([row | {"saldo_apos": None, "vlr": None}]))
            missing = invoke()[1]["financial_context"]
            assert missing["observed"]["entries"][0]["amount_cents"] is None
            assert "balance_after" in missing["missing"]
            (root / "rows.json").write_text("[]")
            assert "transactions_in_window" in invoke()[1]["financial_context"]["missing"]
            (root / "rows.json").write_text(json.dumps([row]))
            # An actual network request from the Broker container still needs service identity and policy.
            probe = '''
import json, urllib.request, urllib.error
from uuid import uuid4
from packages.runtime.http_client import HttpTransport, RemoteFailure
cid=str(uuid4())
payload=dict(schema_version="1.0",request_id=cid,correlation_id=cid,customer_id="competition-client",tool="data.ledger",arguments=dict(kind="ledger",window=dict(from_time="2026-09-01T00:00:00Z",to_time="2026-10-01T00:00:00Z")))
request=urllib.request.Request("http://data:8080/v1/ledger",data=json.dumps(payload).encode(),headers={"Content-Type":"application/json","X-Correlation-ID":cid})
try:
    urllib.request.urlopen(request,timeout=5)
    raise AssertionError("unsigned Data access accepted")
except urllib.error.HTTPError as error:
    assert error.code==403
try:
    HttpTransport()._post("ledger",payload,cid)
    raise AssertionError("Data access without policy proof accepted")
except RemoteFailure as error:
    assert error.code=="POLICY_DENIED"
print("PASS: Data requires Broker identity AND independently validated policy")
'''
            compose("exec", "-T", "tool-broker", "python", "-c", probe)
            for service in ("policy", "tool-broker", "finance", "data"):
                compose("stop", "--timeout", "10", service)
                status, failed = invoke()
                assert status >= 400 or failed.get("status") != "needs_data", (service, failed)
                assert failed.get("financial_result") is None and failed.get("financial_context") is None
                compose("up", "-d", "--no-deps", "--wait", "--wait-timeout", "90", service)
                assert invoke()[1]["financial_context"]["calculated"]["transaction_count"] == 1
            registry["bindings"][0]["context"]["consent_to_analysis"] = False
            (root / "registry.json").write_text(json.dumps(registry))
            assert invoke()[1]["status"] == "denied"
            compose("stop", "--timeout", "15")
            for service in ("web", "api", "agent", "policy", "tool-broker", "finance", "data", "observability"):
                container = compose("ps", "-aq", service)
                state = json.loads(subprocess.check_output(["docker", "inspect", container], text=True))[0]["State"]
                assert state["ExitCode"] == 0 and not state["Running"], service
                assert "shutdown.completed" in compose("logs", "--no-color", service), service
            print("PASS: competition Web/API/Agent/Policy/Broker/Data/Finance, cents, incomplete context, authorization, outages/recovery/shutdown")
        finally:
            compose("down", "--volumes", "--remove-orphans")


if __name__ == "__main__":
    certify()
