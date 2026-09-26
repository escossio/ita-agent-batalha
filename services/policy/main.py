from packages.runtime.server import serve
from .engine import PolicyEngine

engine = PolicyEngine()


def evaluate(payload, correlation_id):
    if payload.get("correlation_id") != correlation_id:
        raise ValueError("correlation mismatch")
    decision = engine.decide(payload)
    return 200, decision.model_dump()


if __name__ == "__main__":
    serve("policy", {"/v1/evaluate": evaluate})
