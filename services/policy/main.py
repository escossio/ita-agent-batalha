import json
from pathlib import Path
from packages.contracts.models import CustomerContext, ToolRequest
from packages.runtime.server import serve
from .engine import PolicyEngine

engine = PolicyEngine()


def evaluate(payload, correlation_id):
    if payload.get("correlation_id") != correlation_id:
        raise ValueError("correlation mismatch")
    decision = engine.decide(payload)
    return 200, decision.model_dump()


def authorize(payload, correlation_id):
    request = ToolRequest.model_validate(payload)
    if request.correlation_id != correlation_id:
        raise ValueError("correlation mismatch")
    contexts = [CustomerContext.model_validate(item) for item in json.loads(
        (Path(__file__).parent / "fixtures/contexts.json").read_text())]
    context = next((item for item in contexts if item.customer_id == request.customer_id), None)
    if context is None:
        context = CustomerContext(schema_version="1.0", customer_id=request.customer_id, mode="DEMO",
                                  consent_to_analysis=False, financial_level="unknown", emotional_state="unknown",
                                  human_requested=False, provenance="DEMO_FIXTURE")
    decision = engine.decide(dict(correlation_id=correlation_id, context=context.model_dump(),
        action="read_snapshot" if request.tool == "data.snapshot" else "project_cashflow", request=request.model_dump()))
    return 200, decision.model_dump()


if __name__ == "__main__":
    serve("policy", {"/v1/evaluate": evaluate, "/v1/authorize": authorize})
