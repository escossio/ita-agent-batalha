"""Agent coordena ports; Policy autoriza, Broker executa, Finance calcula."""
import asyncio
from datetime import datetime, timezone
from uuid import uuid4
from packages.contracts.digests import request_digest
from packages.contracts.models import AgentResponse, PolicyDecision, ToolRequest, ToolResult
from packages.runtime.audit import audit
from .models import AgentInput, ModelPlan, NarrativePlan


def currency(cents):
    # Presentation only: no financial calculation or inference.
    sign = "-" if cents < 0 else ""
    whole, fraction = divmod(abs(cents), 100)
    return f"{sign}R$ {whole:,}".replace(",", ".") + f",{fraction:02}"


class Orchestrator:
    def __init__(self, provider, transport, sink=None):
        self.provider, self.transport, self.sink = provider, transport, sink

    async def run(self, payload):
        value = AgentInput.model_validate(payload)
        base = dict(schema_version="1.0", correlation_id=value.correlation_id,
                    customer_id=value.context.customer_id, mode=value.context.mode, status="error", intent="unknown",
                    message="Não foi possível concluir. Nenhum resultado financeiro foi inventado.",
                    policy_decision_id=None, financial_result=None, tool_results=[], requires_human=False,
                    model_provider=self.provider.name)

        def emit(name, status, **fields):
            audit(value.correlation_id, "agent", name, status, self.sink, **fields)

        def finish(**patch):
            response = AgentResponse.model_validate(base | patch)
            emit("response_validated", "ok")
            return response

        # Restrict on missing consent before exposing even utterance to a model.
        if not value.context.consent_to_analysis:
            return finish(status="denied", message="A análise não foi autorizada.")
        if value.context.human_requested or value.context.emotional_state in {"distressed", "crisis"}:
            return finish(status="handoff", intent="handoff", requires_human=True,
                          message="Podemos buscar apoio humano. Nenhuma ferramenta foi executada.")
        try:
            async with asyncio.timeout(25):
                emit("model_started", "started")
                plan = ModelPlan.model_validate(await self.provider.interpret(value.utterance))
                emit("model_completed", "ok")
                emit("intent_identified", "ok")
                base["intent"] = plan.intent
                if plan.intent == "end_conversation":
                    return finish(status="ok", message="Tudo bem. Encerramos por aqui, sem agendar retorno.")
                if plan.intent == "handoff":
                    emit("handoff_requested", "handoff")
                    return finish(status="handoff", requires_human=True,
                                  message="Podemos buscar apoio humano. Nenhuma ferramenta foi executada.")
                if plan.intent == "unknown":
                    return finish(status="needs_data", message="Ainda não consigo atender essa intenção. Pode esclarecer sua necessidade?")
                if value.context.mode == "COMPETITION" and value.window is None:
                    return finish(status="needs_data", message="Informe a janela temporal do extrato. Não foi presumida uma data de salário.")
                request = ToolRequest(schema_version="1.0", request_id=str(uuid4()),
                    correlation_id=value.correlation_id, customer_id=value.context.customer_id,
                    tool=plan.tool, identity_proof=value.identity_proof,
                    arguments=dict(kind="projection", proposed_spend_cents=value.proposed_spend_cents,
                        ledger_window=value.window.model_dump() if value.context.mode == "COMPETITION" else None))
                decision = PolicyDecision.model_validate(await self.transport.post(
                    "authorize", request.model_dump(), value.correlation_id))
                if (decision.customer_id != value.context.customer_id or decision.correlation_id != value.correlation_id
                        or decision.request_digest != request_digest(request)
                        or datetime.fromisoformat(decision.expires_at.replace("Z", "+00:00")) <= datetime.now(timezone.utc)):
                    raise ValueError("invalid decision binding")
                base["policy_decision_id"] = decision.decision_id
                if decision.outcome != "allow":
                    return finish(status="handoff" if decision.requires_human else "denied",
                                  requires_human=decision.requires_human,
                                  message="Esta ação não foi autorizada." if not decision.requires_human else "É necessário apoio humano.")
                if request.tool not in decision.authorized_tools or "project_cashflow" not in decision.allowed_actions:
                    raise ValueError("missing permission")
                result = ToolResult.model_validate(await self.transport.post(
                    "execute", request.model_dump(), value.correlation_id))
                if (result.request_id != request.request_id or result.correlation_id != value.correlation_id
                        or result.customer_id != value.context.customer_id or result.tool != request.tool):
                    raise ValueError("result binding mismatch")
                base["tool_results"] = [result]
                if result.status != "ok":
                    return finish(status="needs_data" if result.error.code == "MISSING_DATA" else "denied" if result.status == "denied" else "error",
                                  message="Faltam dados para calcular." if result.error.code == "MISSING_DATA" else "A ferramenta não concluiu a operação. Nenhum saldo foi presumido.")
                if result.data.kind == "financial_context":
                    return finish(status="needs_data", financial_context=result.data,
                        message=f"Foram encontrados {result.data.calculated.transaction_count} lançamentos na janela solicitada. Os valores do extrato são observações. "
                        "Faltam saldo atual confirmado, próxima renda e compromissos futuros para projetar. Não foram criadas estimativas ou inferências.")
                projection = result.data
                emit("model_started", "started")
                wording = NarrativePlan.model_validate(await self.provider.compose(
                    "negative" if projection.closing_cents < 0 else "positive", projection.uncertain))
                emit("model_completed", "ok")
                intro = "Vamos olhar com calma." if wording.introduction == "supportive" else "Organizei os dados disponíveis."
                message = f"DEMO — {intro} Antes da próxima renda, em {projection.until}, o saldo projetado fica em {currency(projection.closing_cents)}. "
                if projection.uncertain:
                    message += "Há estimativas; o resultado pode mudar. "
                if projection.closing_cents < 0:
                    message += "Os recursos não cobrem todas as saídas informadas nesse período. "
                message += "A decisão sobre o gasto continua com você."
                return finish(status="ok", message=message, financial_result=projection)
        except Exception:
            emit("error", "error", reason="DEPENDENCY_FAILURE")
            # Invalid/failed model never falls back to invented language or calculations.
            return finish()
