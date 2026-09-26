"""Entradas confiáveis do serviço; nunca preenchidas por grants do modelo."""
from typing import Annotated, Literal
from pydantic import Field, model_validator
from packages.contracts.models import (
    Action, CorrelationID, CustomerContext, Eligibility, Product, Record, ToolName, ToolRequest,
)


class Facts(Record):
    inadimplente: bool | None = None
    renegociacao_elegivel: bool | None = None
    risco_saldo_negativo: bool | None = None
    necessidade: Literal["liquidez", "reserva", "investimento", "aquisição"] | None = None
    credito_elegivel: bool | None = None
    capacidade_pagamento: bool | None = None
    objetivo: Literal["aquisição", "reserva", "investimento"] | None = None
    urgencia: Literal["ALTA", "BAIXA"] | None = None
    financiamento_elegivel: bool | None = None
    consorcio_elegivel: bool | None = None
    sobra_recorrente: bool | None = None
    reserva: bool | None = None
    objetivo_definido: bool | None = None
    parcela_terminou: bool | None = None
    aumento_renda_detectado: bool | None = None
    recorrencia_confirmada: bool | None = None
    recuperacao_financeira: bool | None = None
    produto_elegivel: bool | None = None
    necessidade_aderente: bool | None = None
    multiplos_produtos_elegiveis: bool | None = None
    costs_verified: bool = False
    profile_verified: bool = False
    horizon_verified: bool = False
    liquidity_compatible: bool = False


class PolicyInput(Record):
    correlation_id: CorrelationID
    context: CustomerContext
    action: Action
    request: ToolRequest | None = None
    eligibility: Eligibility | None = None
    facts: Facts = Facts()
    requested_products: Annotated[list[Product], Field(max_length=5)] = []
    proactive: bool = False
    user_declined: bool = False

    @model_validator(mode="after")
    def binding(self):
        if self.request is not None:
            expected = "read_snapshot" if self.request.tool == "data.snapshot" else "project_cashflow"
            if self.action != expected or self.request.customer_id != self.context.customer_id or self.request.correlation_id != self.correlation_id:
                raise ValueError("policy request identity/action mismatch")
        if self.eligibility is not None and self.eligibility.customer_id != self.context.customer_id:
            raise ValueError("eligibility customer mismatch")
        if len(set(self.requested_products)) != len(self.requested_products):
            raise ValueError("duplicate requested products")
        return self


class PolicyLimits(Record):
    service_enabled: bool = True
    blocked_products: list[Product] = []
    blocked_tools: list[ToolName] = []
    eligibility_max_age_seconds: Annotated[int, Field(ge=1, le=86400)] = 86400
