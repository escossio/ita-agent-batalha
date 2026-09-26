from packages.contracts.models import ToolRequest
from packages.runtime.audit import audit
from packages.runtime.server import serve
from .store import initialize, read_snapshot, ready


def snapshot(payload, correlation_id):
    request = ToolRequest.model_validate(payload)
    if request.correlation_id != correlation_id or request.tool != "data.snapshot":
        raise ValueError("invalid snapshot request")
    value = read_snapshot(request.customer_id)
    if value is None:
        return 422, {"error": "MISSING_DATA", "retryable": False}
    audit(correlation_id, "data", "tool_completed", "ok", tool="data.snapshot")
    return 200, value.model_dump()


if __name__ == "__main__":
    initialize()
    serve("data", {"/v1/snapshot": snapshot}, health=ready)
