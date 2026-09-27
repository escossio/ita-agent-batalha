import json
import os
from datetime import datetime
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
    is_external = request.tool == "data.ledger" or (request.tool == "finance.project" and request.arguments.ledger_window is not None)
    if os.getenv("ITA_RUNTIME_MODE", "demo") == "competition":
        from packages.runtime.identities import for_customer
        from packages.runtime.service_auth import verify_identity
        try:
            binding = for_customer(request.customer_id)
            context = binding.context
            claims = verify_identity(request.identity_proof)
            window = request.arguments.window if request.tool == "data.ledger" else request.arguments.ledger_window
            days = (datetime.fromisoformat(window.to_time.replace("Z", "+00:00")) - datetime.fromisoformat(window.from_time.replace("Z", "+00:00"))).total_seconds() / 86400
            if (not is_external or claims["customer_id"] != request.customer_id or claims["correlation_id"] != correlation_id
                    or claims["window"] != window.model_dump() or claims["session_hash"] != binding.session_hash
                    or days > binding.max_window_days or (request.tool == "finance.project" and
                    claims["proposed_spend_cents"] != request.arguments.proposed_spend_cents)):
                raise PermissionError()
        except Exception:
            context = context.model_copy(update={"consent_to_analysis": False})
    elif is_external:
        context = context.model_copy(update={"consent_to_analysis": False})
    decision = engine.decide(dict(correlation_id=correlation_id, context=context.model_dump(),
        action={"data.snapshot": "read_snapshot", "data.ledger": "read_ledger", "finance.project": "project_cashflow"}[request.tool], request=request.model_dump()))
    return 200, decision.model_dump()


if __name__ == "__main__":
    serve("policy", {"/v1/evaluate": evaluate, "/v1/authorize": authorize})
