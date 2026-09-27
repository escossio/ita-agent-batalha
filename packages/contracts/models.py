"""Protocolo 1.0: validação estrita, sem autoridade financeira no LLM."""

from typing import Annotated, Literal

from pydantic import Field, model_validator


from .base import Contract, Record, Identifier, CorrelationID, Digest, Day, Timestamp, Money, Amount
from .ledger import CompetitionLedger, LedgerWindow, FinancialContext

Product = Literal["credit", "renegotiation", "financing", "consortium", "investment"]
ToolName = Literal["data.snapshot", "finance.project", "data.ledger"]
Action = Literal["read_snapshot", "read_ledger", "project_cashflow", "compare_products", "end_conversation", "handoff"]
Reason = Literal[
    "ALLOWED", "DEFAULT_DENY", "NO_CONSENT", "HUMAN_REQUESTED", "PERSON_SAFETY",
    "UNKNOWN_CONTEXT", "FINANCIAL_DISTRESS", "INELIGIBLE", "PRODUCT_BLOCKED",
    "TOOL_NOT_ALLOWED", "INVALID_INPUT", "MISSING_DATA", "UNCERTAIN_DATA",
    "DEPENDENCY_FAILURE", "TIMEOUT", "INVALID_OUTPUT", "USER_DECLINED",
]


class CustomerContext(Contract):
    customer_id: Identifier
    mode: Literal["DEMO", "COMPETITION"]
    consent_to_analysis: bool
    financial_level: Literal["unknown", "critical", "tight", "stable"]
    emotional_state: Literal["unknown", "neutral", "distressed", "crisis"]
    human_requested: bool
    contact_permission: bool = False
    locale: Literal["pt-BR"] = "pt-BR"
    provenance: Literal["DEMO_FIXTURE", "VERIFIED_RUNTIME_IDENTITY"]


    @model_validator(mode="after")
    def identity_provenance(self):
        if (self.mode == "COMPETITION") != (self.provenance == "VERIFIED_RUNTIME_IDENTITY"):
            raise ValueError("context mode/provenance mismatch")
        return self


class Income(Record):
    due_on: Day
    amount_cents: Amount
    recurring_confirmed: bool
    certainty: Literal["confirmed", "estimated"]


class Commitment(Record):
    entry_id: Identifier
    due_on: Day
    amount_cents: Amount
    category: Literal["bill", "installment", "subscription", "recurring", "variable"]
    certainty: Literal["confirmed", "estimated"]
    installment_number: Annotated[int, Field(ge=1, le=600)] | None = None
    installment_count: Annotated[int, Field(ge=1, le=600)] | None = None

    @model_validator(mode="after")
    def installment_bounds(self):
        if (self.installment_number is None) != (self.installment_count is None):
            raise ValueError("installment number and count must be provided together")
        if self.installment_number is not None:
            if self.category != "installment" or self.installment_number > self.installment_count:
                raise ValueError("invalid installment sequence")
        return self


class HistoricalPeriod(Record):
    month: Annotated[str, Field(pattern=r"^\d{4}-(0[1-9]|1[0-2])$")]
    income_cents: Amount
    committed_cents: Amount
    variable_cents: Amount
    installment_cents: Amount
    negative_days: Annotated[int, Field(ge=0, le=31)]
    complete: bool


class FinancialSnapshot(Contract):
    kind: Literal["financial_snapshot"]
    snapshot_id: Identifier
    customer_id: Identifier
    mode: Literal["DEMO"]
    as_of: Day
    currency: Literal["BRL"]
    balance_cents: Money
    next_income: Income | None
    commitments: Annotated[list[Commitment], Field(max_length=1000)]
    history: Annotated[list[HistoricalPeriod], Field(max_length=36)] | None
    data_complete: bool
    provenance: Literal["DEMO_FIXTURE"]

    @model_validator(mode="after")
    def temporal_integrity(self):
        if self.next_income is not None and self.next_income.due_on <= self.as_of:
            raise ValueError("next income must be after as_of")
        if len({item.entry_id for item in self.commitments}) != len(self.commitments):
            raise ValueError("duplicate commitment IDs")
        if self.history is not None and len({item.month for item in self.history}) != len(self.history):
            raise ValueError("duplicate historical periods")
        return self


class ProductEligibility(Record):
    product: Product
    status: Literal["eligible", "ineligible", "unknown"]
    source: Literal["DEMO_FIXTURE"]


class Eligibility(Contract):
    customer_id: Identifier
    assessed_at: Timestamp
    products: Annotated[list[ProductEligibility], Field(max_length=5)]

    @model_validator(mode="after")
    def no_duplicates(self):
        if len({item.product for item in self.products}) != len(self.products):
            raise ValueError("duplicate product eligibility")
        return self


class PolicyDecision(Contract):
    decision_id: CorrelationID
    correlation_id: CorrelationID
    customer_id: Identifier
    request_digest: Digest
    outcome: Literal["allow", "deny", "handoff"]
    allowed_actions: Annotated[list[Action], Field(max_length=6)]
    blocked_actions: Annotated[list[Action], Field(max_length=6)]
    allowed_products: Annotated[list[Product], Field(max_length=5)]
    blocked_products: Annotated[list[Product], Field(max_length=5)]
    authorized_tools: Annotated[list[ToolName], Field(max_length=3)]
    credit_allowed: bool
    max_options: Annotated[int, Field(ge=0, le=5)]
    requires_human: bool
    language_constraints: Annotated[list[Literal[
        "no_judgment", "no_invented_numbers", "no_pressure", "signal_uncertainty", "no_product_offer",
    ]], Field(max_length=5)]
    reasons: Annotated[list[Reason], Field(min_length=1, max_length=10)]
    policy_version: Literal["1.0"]
    expires_at: Timestamp

    @model_validator(mode="after")
    def coherent_authorization(self):
        if self.outcome != "allow" and (self.allowed_actions or self.allowed_products or self.authorized_tools or self.credit_allowed or self.max_options):
            raise ValueError("deny/handoff cannot grant authority")
        if self.outcome == "handoff" and not self.requires_human:
            raise ValueError("handoff requires human")
        if set(self.allowed_actions) & set(self.blocked_actions):
            raise ValueError("action simultaneously allowed and blocked")
        if set(self.allowed_products) & set(self.blocked_products):
            raise ValueError("product simultaneously allowed and blocked")
        if self.credit_allowed != ("credit" in self.allowed_products):
            raise ValueError("credit permission must match product permission")
        return self


class SnapshotArguments(Record):
    kind: Literal["snapshot"]


class LedgerArguments(Record):
    kind: Literal["ledger"]
    window: LedgerWindow


class ProjectionArguments(Record):
    kind: Literal["projection"]
    proposed_spend_cents: Amount
    ledger_window: LedgerWindow | None = None


class ToolRequest(Contract):
    request_id: CorrelationID
    correlation_id: CorrelationID
    customer_id: Identifier
    tool: ToolName
    identity_proof: Annotated[str, Field(max_length=4096)] | None = None
    arguments: Annotated[SnapshotArguments | ProjectionArguments | LedgerArguments, Field(discriminator="kind")]
    # Trace only: Broker must independently enforce Policy, never trust caller grants.
    policy_decision_id: CorrelationID | None = None

    @model_validator(mode="after")
    def matching_arguments(self):
        expected = {"data.snapshot": "snapshot", "data.ledger": "ledger", "finance.project": "projection"}[self.tool]
        if self.arguments.kind != expected:
            raise ValueError("tool/arguments mismatch")
        return self


class Projection(Record):
    kind: Literal["projection"]
    customer_id: Identifier
    currency: Literal["BRL"]
    snapshot_id: Identifier
    as_of: Day
    until: Day
    opening_cents: Money
    commitments_cents: Amount
    estimates_cents: Amount
    proposed_spend_cents: Amount
    base_closing_cents: Money
    closing_cents: Money
    lowest_balance_cents: Money
    uncertain: bool
    warnings: Annotated[list[Reason], Field(max_length=10)]


    @model_validator(mode="after")
    def financial_consistency(self):
        if self.until <= self.as_of:
            raise ValueError("invalid projection horizon")
        if self.base_closing_cents != self.opening_cents - self.commitments_cents - self.estimates_cents:
            raise ValueError("inconsistent base projection")
        if self.closing_cents != self.base_closing_cents - self.proposed_spend_cents:
            raise ValueError("inconsistent spending projection")
        if self.lowest_balance_cents != self.closing_cents:
            raise ValueError("invalid lowest balance for outflow-only horizon")
        if self.estimates_cents and not self.uncertain:
            raise ValueError("estimates cannot be certain")
        if self.uncertain != ("UNCERTAIN_DATA" in self.warnings):
            raise ValueError("uncertainty must be explicit")
        return self


class ToolError(Record):
    code: Literal["POLICY_DENIED", "POLICY_UNAVAILABLE", "INVALID_INPUT", "INVALID_OUTPUT", "MISSING_DATA", "DEPENDENCY_UNAVAILABLE", "TIMEOUT", "NOT_IMPLEMENTED", "SOURCE_AUTHENTICATION_FAILED", "SOURCE_SCHEMA_MISMATCH", "SOURCE_REGION_MISMATCH", "SOURCE_NOT_FOUND", "SOURCE_INVALID_DATA"]
    retryable: bool


class ToolResult(Contract):
    request_id: CorrelationID
    correlation_id: CorrelationID
    customer_id: Identifier
    tool: ToolName
    status: Literal["ok", "error", "denied", "timeout"]
    duration_ms: Annotated[int, Field(ge=0, le=3600000)]
    data: Annotated[FinancialSnapshot | Projection | CompetitionLedger | FinancialContext, Field(discriminator="kind")] | None
    error: ToolError | None

    @model_validator(mode="after")
    def matching_result(self):
        if self.status == "ok":
            if self.error is not None or self.data is None:
                raise ValueError("success requires data and no error")
            expected = {"data.snapshot": {"financial_snapshot"}, "data.ledger": {"competition_ledger"}, "finance.project": {"projection", "financial_context"}}[self.tool]
            if self.data.kind not in expected:
                raise ValueError("tool/result mismatch")
            if self.data.customer_id != self.customer_id:
                raise ValueError("tool/customer mismatch")
        elif self.data is not None or self.error is None:
            raise ValueError("failure requires error and no financial data")
        return self


class AgentResponse(Contract):
    financial_context: FinancialContext | None = None
    model_provider: Literal["mock", "vertex"] | None = None
    correlation_id: CorrelationID
    customer_id: Identifier
    mode: Literal["DEMO", "COMPETITION"]
    status: Literal["ok", "needs_data", "denied", "handoff", "error"]
    intent: Literal["project_cashflow", "unknown", "end_conversation", "handoff"]
    message: Annotated[str, Field(min_length=1, max_length=2000)]
    policy_decision_id: CorrelationID | None
    financial_result: Projection | None
    tool_results: Annotated[list[ToolResult], Field(max_length=10)]
    requires_human: bool

    @model_validator(mode="after")
    def response_integrity(self):
        if self.financial_context is not None:
            if self.status != "needs_data" or self.financial_result is not None or self.mode != "COMPETITION":
                raise ValueError("incomplete context cannot claim projection")
            if not any(r.status == "ok" and r.data == self.financial_context for r in self.tool_results):
                raise ValueError("context requires successful tool evidence")
        if self.status != "ok" and self.financial_result is not None:
            raise ValueError("unsuccessful response cannot claim calculated results")
        if self.financial_result is not None and not any(
            result.status == "ok" and result.data == self.financial_result for result in self.tool_results
        ):
            raise ValueError("financial result requires matching successful tool evidence")
        if any(result.correlation_id != self.correlation_id for result in self.tool_results):
            raise ValueError("correlation mismatch")
        if any(result.customer_id != self.customer_id for result in self.tool_results):
            raise ValueError("customer mismatch")
        if self.status == "handoff" and not self.requires_human:
            raise ValueError("handoff must be explicit")
        return self


class AuditEvent(Contract):
    event_id: CorrelationID
    correlation_id: CorrelationID
    occurred_at: Timestamp
    component: Literal["api", "agent", "policy", "tool-broker", "finance", "data"]
    event: Literal[
        "request_received", "intent_identified", "policy_requested", "policy_decided",
        "tool_requested", "tool_authorized", "tool_blocked", "tool_completed",
        "calculation_started", "calculation_completed", "model_started", "model_completed",
        "response_validated", "handoff_requested", "request_completed", "error",
    ]
    status: Literal["started", "ok", "denied", "error", "timeout", "handoff"]
    tool: ToolName | None = None
    duration_ms: Annotated[int, Field(ge=0, le=3600000)] | None = None
    reason: Reason | None = None
    payload_digest: Digest | None = None


CONTRACTS = (CustomerContext, FinancialSnapshot, Eligibility, PolicyDecision,
             ToolRequest, ToolResult, AgentResponse, AuditEvent)
