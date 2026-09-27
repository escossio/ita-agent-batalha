"""Única porta de execução. Decisões do chamador nunca são autoridade."""
import asyncio
from datetime import datetime, timezone
from time import monotonic
from uuid import uuid4
from pydantic import ValidationError
from packages.contracts.digests import request_digest
from packages.contracts.ledger import CompetitionLedger, FinancialContext
from packages.contracts.models import FinancialSnapshot, PolicyDecision, Projection, ToolRequest, ToolResult
from packages.runtime.audit import audit
from packages.runtime.http_client import RemoteFailure


class Broker:
    def __init__(self, transport, sink=None, timeout_seconds=10):
        if not 0 < timeout_seconds <= 10:
            raise ValueError("invalid timeout")
        self.transport, self.sink, self.timeout = transport, sink, timeout_seconds

    def emit(self, request, name, status, **fields):
        audit(request.correlation_id, "tool-broker", name, status, self.sink, tool=request.tool, **fields)

    async def authorized(self, request):
        self.emit(request, "policy_requested", "started")
        try:
            raw = await self.transport.post("authorize", request.model_dump(), request.correlation_id)
            decision = PolicyDecision.model_validate(raw)
        except TimeoutError:
            raise
        except Exception:
            raise RemoteFailure("POLICY_UNAVAILABLE") from None
        if (decision.correlation_id != request.correlation_id or decision.customer_id != request.customer_id
                or decision.request_digest != request_digest(request)
                or datetime.fromisoformat(decision.expires_at.replace("Z", "+00:00")) <= datetime.now(timezone.utc)):
            raise RemoteFailure("POLICY_UNAVAILABLE")
        self.emit(request, "policy_decided", "ok" if decision.outcome == "allow" else "denied",
                  reason=decision.reasons[0])
        action = {"data.snapshot": "read_snapshot", "data.ledger": "read_ledger", "finance.project": "project_cashflow"}[request.tool]
        if decision.outcome != "allow" or request.tool not in decision.authorized_tools or action not in decision.allowed_actions:
            raise RemoteFailure("POLICY_DENIED")
        self.emit(request, "tool_authorized", "ok")

    async def snapshot(self, request):
        await self.authorized(request)
        raw = await self.transport.post("snapshot", request.model_dump(), request.correlation_id)
        value = FinancialSnapshot.model_validate(raw)
        if value.customer_id != request.customer_id:
            raise RemoteFailure("INVALID_OUTPUT")
        return value

    async def execute(self, payload):
        request = ToolRequest.model_validate(payload)
        start = monotonic()
        self.emit(request, "tool_requested", "started")
        data, error, status = None, None, "ok"
        try:
            async with asyncio.timeout(self.timeout):
                if request.tool == "data.snapshot":
                    data = await self.snapshot(request)
                elif request.tool == "data.ledger":
                    await self.authorized(request)
                    raw = await self.transport.post("ledger", request.model_dump(), request.correlation_id)
                    data = CompetitionLedger.model_validate(raw)
                    if (data.customer_id != request.customer_id or data.correlation_id != request.correlation_id
                            or data.from_time != request.arguments.window.from_time or data.to_time != request.arguments.window.to_time):
                        raise RemoteFailure("INVALID_OUTPUT")
                elif request.tool == "finance.project" and request.arguments.ledger_window is not None:
                    await self.authorized(request)
                    child = ToolRequest(schema_version="1.0", request_id=str(uuid4()), correlation_id=request.correlation_id,
                        customer_id=request.customer_id, tool="data.ledger", identity_proof=request.identity_proof,
                        arguments={"kind": "ledger", "window": request.arguments.ledger_window.model_dump()})
                    nested = await self.execute(child.model_dump())
                    if nested.status != "ok":
                        raise RemoteFailure(nested.error.code)
                    raw = await self.transport.post("assess", dict(correlation_id=request.correlation_id,
                        ledger=nested.data.model_dump()), request.correlation_id)
                    data = FinancialContext.model_validate(raw)
                    if data.observed != nested.data:
                        raise RemoteFailure("INVALID_OUTPUT")
                elif request.tool == "finance.project":
                    await self.authorized(request)
                    child = ToolRequest(schema_version="1.0", request_id=str(uuid4()),
                                        correlation_id=request.correlation_id, customer_id=request.customer_id,
                                        tool="data.snapshot", arguments={"kind": "snapshot"})
                    # Every dependent capability has its own authorization; no hidden bypass.
                    nested = await self.execute(child.model_dump())
                    if nested.status != "ok":
                        raise RemoteFailure(nested.error.code)
                    snapshot = nested.data
                    raw = await self.transport.post("project", dict(correlation_id=request.correlation_id,
                        snapshot=snapshot.model_dump(), proposed_spend_cents=request.arguments.proposed_spend_cents),
                        request.correlation_id)
                    data = Projection.model_validate(raw)
                    if (data.customer_id != request.customer_id or data.snapshot_id != snapshot.snapshot_id
                            or data.opening_cents != snapshot.balance_cents
                            or data.as_of != snapshot.as_of or snapshot.next_income is None
                            or data.until != snapshot.next_income.due_on
                            or data.proposed_spend_cents != request.arguments.proposed_spend_cents):
                        raise RemoteFailure("INVALID_OUTPUT")
                else:
                    raise RemoteFailure("INVALID_INPUT")
        except TimeoutError:
            status, error = "timeout", dict(code="TIMEOUT", retryable=True)
        except ValidationError:
            status, error = "error", dict(code="INVALID_OUTPUT", retryable=False)
        except RemoteFailure as failure:
            status = "denied" if failure.code == "POLICY_DENIED" else "timeout" if failure.code == "TIMEOUT" else "error"
            error = dict(code=failure.code, retryable=failure.code in {"TIMEOUT", "DEPENDENCY_UNAVAILABLE", "POLICY_UNAVAILABLE"})
        except Exception:
            status, error = "error", dict(code="DEPENDENCY_UNAVAILABLE", retryable=True)
        if status != "ok":
            data = None
        elapsed = min(round((monotonic() - start) * 1000), 3600000)
        result = ToolResult(schema_version="1.0", request_id=request.request_id, correlation_id=request.correlation_id,
                            customer_id=request.customer_id, tool=request.tool, status=status,
                            duration_ms=elapsed, data=data, error=error)
        self.emit(request, "tool_blocked" if status == "denied" else "tool_completed", status,
                  duration_ms=elapsed)
        return result
