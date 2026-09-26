"""Adaptador DEMO explícito da etapa 9; persistência PostgreSQL na etapa 11."""
from pathlib import Path
from packages.contracts.models import FinancialSnapshot, ToolRequest
from packages.runtime.server import serve


def snapshot(payload, correlation_id):
    request = ToolRequest.model_validate(payload)
    if request.correlation_id != correlation_id or request.tool != "data.snapshot":
        raise ValueError("invalid snapshot request")
    # Fixed path; user/model cannot select files, URLs or SQL.
    value = FinancialSnapshot.model_validate_json((Path(__file__).parent / "fixtures/demo-snapshot.json").read_text())
    if value.customer_id != request.customer_id:
        return 422, {"error": "MISSING_DATA", "retryable": False}
    return 200, value.model_dump()


if __name__ == "__main__":
    serve("data", {"/v1/snapshot": snapshot})
