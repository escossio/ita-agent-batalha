import asyncio
import os
import time
from packages.contracts.models import AgentResponse, CustomerContext
from packages.runtime.audit import audit
from packages.runtime.http_client import HttpTransport
from packages.runtime.server import serve, request_headers
from .models import ChatInput


class ApiTransport(HttpTransport):
    ROUTES = {"respond": "http://agent:8080/v1/respond"}
    TIMEOUT = 28


async def chat_async(payload, correlation_id, transport=None):
    value = ChatInput.model_validate(payload)
    customer = {"standard": "demo-customer", "denied": "demo-denied", "crisis": "demo-crisis"}[value.demo_case]
    context = CustomerContext(schema_version="1.0", customer_id=customer, mode="DEMO",
        consent_to_analysis=value.consent_to_analysis and value.demo_case != "denied", financial_level="stable",
        emotional_state="crisis" if value.demo_case == "crisis" else "neutral", human_requested=False,
        provenance="DEMO_FIXTURE")
    identity_proof = None
    if os.getenv("ITA_RUNTIME_MODE", "demo") == "competition":
        from packages.runtime.identities import authenticate
        from packages.runtime.service_auth import sign_identity
        binding = authenticate(request_headers.get())
        customer = binding.context.customer_id
        context = binding.context.model_copy(update={"consent_to_analysis": binding.context.consent_to_analysis and value.consent_to_analysis})
        if value.window is not None and context.consent_to_analysis:
            identity_proof = sign_identity(dict(customer_id=customer, correlation_id=correlation_id,
                window=value.window.model_dump(), proposed_spend_cents=value.amount_cents(),
                expires=int(time.time()) + 30, session_hash=binding.session_hash))
    audit(correlation_id, "api", "request_received", "started")
    raw = await (transport or ApiTransport()).post("respond", dict(schema_version="1.0", correlation_id=correlation_id,
        context=context.model_dump(), utterance=value.utterance, proposed_spend_cents=value.amount_cents(),
        window=value.window.model_dump() if value.window else None, identity_proof=identity_proof), correlation_id)
    response = AgentResponse.model_validate(raw)
    if response.correlation_id != correlation_id or response.customer_id != customer:
        raise ValueError("agent response identity mismatch")
    audit(correlation_id, "api", "request_completed", "ok" if response.status == "ok" else "error")
    return response


def chat(payload, correlation_id):
    return 200, asyncio.run(chat_async(payload, correlation_id)).model_dump()


if __name__ == "__main__":
    serve("api", {"/v1/chat": chat})
