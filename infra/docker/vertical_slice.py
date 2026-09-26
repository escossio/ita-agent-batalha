"""Integração completa, incluindo prova de persistência; somente worker."""
import json
import subprocess
import urllib.request
from uuid import uuid4


def compose(*args):
    return subprocess.check_output(["docker", "compose", *args], text=True).strip()


def request(address, consent=True):
    cid = str(uuid4())
    query = urllib.request.Request(f"http://{address}/api/chat", data=json.dumps(dict(
        utterance="Até o próximo salário dá?", amount_brl="500,00", consent_to_analysis=consent)).encode(),
        headers={"Content-Type": "application/json", "X-Correlation-ID": cid})
    with urllib.request.urlopen(query, timeout=35) as response:
        assert response.headers["X-Correlation-ID"] == cid
        result = json.load(response)
    assert result["correlation_id"] == cid
    return result


if __name__ == "__main__":
    address = compose("port", "web", "8080")
    with urllib.request.urlopen(f"http://{address}/", timeout=5) as response:
        assert "Até o próximo" in response.read().decode()
    result = request(address)
    assert result["status"] == "ok", result
    assert result["financial_result"]["closing_cents"] == 60000
    assert result["model_provider"] == "mock"
    assert result["policy_decision_id"]
    assert result["tool_results"][0]["status"] == "ok"
    # Update actual PostgreSQL through Data's credential; never change frontend or fixture file.
    mutation = """
from component.store import connect
with connect() as connection:
    connection.execute("UPDATE demo_snapshots SET payload = jsonb_set(payload, '{balance_cents}', %s::jsonb) WHERE customer_id = %s", ('210000','demo-customer'))
"""
    restore = mutation.replace("210000", "200000")
    try:
        compose("exec", "-T", "data", "python", "-c", mutation)
        assert request(address)["financial_result"]["closing_cents"] == 70000
    finally:
        compose("exec", "-T", "data", "python", "-c", restore)
    denied = request(address, False)
    assert denied["status"] == "denied" and denied["financial_result"] is None
    logs = compose("logs", "--no-color", "api", "agent", "tool-broker", "data")
    assert result["correlation_id"] in logs
    print("PASS: Web/API/Agent/Policy/Broker/Finance/Data/PostgreSQL, database mutation, consent, audit")
