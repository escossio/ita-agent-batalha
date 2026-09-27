from packages.runtime.server import serve
from .engine import MissingData, project
from .ledger import assess


def calculate(payload, correlation_id):
    if payload.get("correlation_id") != correlation_id:
        raise ValueError("correlation mismatch")
    try:
        result = project(payload)
    except MissingData:
        return 422, {"error": "MISSING_DATA", "retryable": False}
    return 200, result.model_dump()


if __name__ == "__main__":
    serve("finance", {"/v1/project": calculate, "/v1/assess-ledger": assess})
