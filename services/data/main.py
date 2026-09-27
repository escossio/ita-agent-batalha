import os
import json
from .normalization import SourceDataError
from datetime import datetime, timezone
from packages.contracts.models import ToolRequest, PolicyDecision
from packages.contracts.ledger import LedgerReadRequest, CompetitionLedger
from packages.contracts.digests import request_digest
from packages.runtime.http_client import HttpTransport
from packages.runtime.identities import for_customer
from packages.runtime.service_auth import BrokerAuthenticator
from .ledger_runtime import configured_reader
from packages.runtime.audit import audit
from packages.runtime.server import serve
from .store import initialize, read_snapshot, ready


def reauthorize(request):
    raw = HttpTransport()._post("authorize", request.model_dump(), request.correlation_id)
    decision = PolicyDecision.model_validate(raw)
    action = {"data.snapshot": "read_snapshot", "data.ledger": "read_ledger"}[request.tool]
    if (decision.outcome != "allow" or request.tool not in decision.authorized_tools or action not in decision.allowed_actions
            or decision.customer_id != request.customer_id or decision.correlation_id != request.correlation_id
            or decision.request_digest != request_digest(request)
            or datetime.fromisoformat(decision.expires_at.replace("Z", "+00:00")) <= datetime.now(timezone.utc)):
        raise PermissionError("DATA_POLICY_DENIED")


def ledger(payload, correlation_id):
    request = ToolRequest.model_validate(payload)
    if request.correlation_id != correlation_id or request.tool != "data.ledger":
        raise ValueError("invalid ledger request")
    reauthorize(request)
    binding = for_customer(request.customer_id)
    query = LedgerReadRequest(schema_version="1.0", correlation_id=correlation_id, customer_id=request.customer_id,
        source_user_id=binding.source_user_id, **request.arguments.window.model_dump())
    try:
        value = configured_reader().read(query.model_dump())
    except SourceDataError as error:
        code = {"BIGQUERY_AUTHENTICATION_FAILED": "SOURCE_AUTHENTICATION_FAILED",
                "BIGQUERY_SCHEMA_DRIFT": "SOURCE_SCHEMA_MISMATCH", "BIGQUERY_LOCATION_MISMATCH": "SOURCE_REGION_MISMATCH",
                "BIGQUERY_SOURCE_NOT_FOUND": "SOURCE_NOT_FOUND", "BIGQUERY_QUERY_TIMEOUT": "TIMEOUT"}.get(str(error), "SOURCE_INVALID_DATA")
        audit(correlation_id, "data", "error", "timeout" if code == "TIMEOUT" else "error", tool="data.ledger", reason="DEPENDENCY_FAILURE")
        return 504 if code == "TIMEOUT" else 503, {"error": code, "retryable": code == "TIMEOUT"}
    if len(json.dumps(value.model_dump()).encode()) > 90000:
        return 503, {"error": "SOURCE_INVALID_DATA", "retryable": False}
    if os.environ["ITA_DATA_PROVIDER"] == "bigquery_mock":
        value = CompetitionLedger.model_validate(value.model_dump() | {"provenance": "COMPETITION_SYNTHETIC_BIGQUERY_MOCK"})
    audit(correlation_id, "data", "tool_completed", "ok", tool="data.ledger")
    return 200, value.model_dump()


def snapshot(payload, correlation_id):
    request = ToolRequest.model_validate(payload)
    if request.correlation_id != correlation_id or request.tool != "data.snapshot":
        raise ValueError("invalid snapshot request")
    reauthorize(request)
    if os.getenv("ITA_DATA_PROVIDER", "postgres") != "postgres":
        raise PermissionError("DEMO_SNAPSHOT_DISABLED")
    value = read_snapshot(request.customer_id)
    if value is None:
        return 422, {"error": "MISSING_DATA", "retryable": False}
    audit(correlation_id, "data", "tool_completed", "ok", tool="data.snapshot")
    return 200, value.model_dump()


if __name__ == "__main__":
    mode = os.getenv("ITA_DATA_PROVIDER", "postgres")
    if mode == "postgres":
        initialize()
    else:
        configured_reader()
    serve("data", {"/v1/snapshot": snapshot, "/v1/ledger": ledger},
          health=ready if mode == "postgres" else None, before_route=BrokerAuthenticator())
