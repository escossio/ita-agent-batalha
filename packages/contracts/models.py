"""Protocolo 1.0: validação estrita, sem autoridade financeira no LLM."""

from datetime import date, datetime
from typing import Annotated, Literal

from pydantic import AfterValidator, BaseModel, ConfigDict, Field, model_validator


def calendar_date(value: str) -> str:
    date.fromisoformat(value)
    return value


def utc_timestamp(value: str) -> str:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None or parsed.utcoffset().total_seconds() != 0:
        raise ValueError("UTC timestamp required")
    return value


Identifier = Annotated[str, Field(pattern=r"^[a-zA-Z0-9][a-zA-Z0-9_-]{0,63}$")]
CorrelationID = Annotated[str, Field(pattern=r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$")]
Digest = Annotated[str, Field(pattern=r"^[0-9a-f]{64}$")]
Day = Annotated[str, Field(pattern=r"^\d{4}-\d{2}-\d{2}$"), AfterValidator(calendar_date)]
Timestamp = Annotated[str, Field(max_length=32), AfterValidator(utc_timestamp)]
Money = Annotated[int, Field(ge=-10**12, le=10**12)]
Amount = Annotated[int, Field(ge=0, le=10**12)]
Product = Literal["credit", "renegotiation", "financing", "consortium", "investment"]
ToolName = Literal["data.snapshot", "finance.project"]
Action = Literal["read_snapshot", "project_cashflow", "compare_products", "end_conversation", "handoff"]
Reason = Literal[
    "ALLOWED", "DEFAULT_DENY", "NO_CONSENT", "HUMAN_REQUESTED", "PERSON_SAFETY",
    "UNKNOWN_CONTEXT", "FINANCIAL_DISTRESS", "INELIGIBLE", "PRODUCT_BLOCKED",
    "TOOL_NOT_ALLOWED", "INVALID_INPUT", "MISSING_DATA", "UNCERTAIN_DATA",
    "DEPENDENCY_FAILURE", "TIMEOUT", "INVALID_OUTPUT", "USER_DECLINED",
]


class Record(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, frozen=True, validate_default=True)


class Contract(Record):
    schema_version: Literal["1.0"]


class CustomerContext(Contract):
    customer_id: Identifier
    mode: Literal["DEMO"]
    consent_to_analysis: bool
    financial_level: Literal["unknown", "critical", "tight", "stable"]
    emotional_state: Literal["unknown", "neutral", "distressed", "crisis"]
    human_requested: bool
    contact_permission: bool = False
    locale: Literal["pt-BR"] = "pt-BR"
    provenance: Literal["DEMO_FIXTURE"]


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
    allowed_actions: Annotated[list[Action], Field(max_length=5)]
    blocked_actions: Annotated[list[Action], Field(max_length=5)]
    allowed_products: Annotated[list[Product], Field(max_length=5)]
    blocked_products: Annotated[list[Product], Field(max_length=5)]
    authorized_tools: Annotated[list[ToolName], Field(max_length=2)]
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


class ProjectionArguments(Record):
    kind: Literal["projection"]
    proposed_spend_cents: Amount


class ToolRequest(Contract):
    request_id: CorrelationID
    correlation_id: CorrelationID
    customer_id: Identifier
    tool: ToolName
    arguments: Annotated[SnapshotArguments | ProjectionArguments, Field(discriminator="kind")]
    # Trace only: Broker must independently enforce Policy, never trust caller grants.
    policy_decision_id: CorrelationID | None = None

    @model_validator(mode="after")
    def matching_arguments(self):
        expected = "snapshot" if self.tool == "data.snapshot" else "projection"
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


class ToolError(Record):
    code: Literal["POLICY_DENIED", "POLICY_UNAVAILABLE", "INVALID_INPUT", "INVALID_OUTPUT", "MISSING_DATA", "DEPENDENCY_UNAVAILABLE", "TIMEOUT", "NOT_IMPLEMENTED"]
    retryable: bool


class ToolResult(Contract):
    request_id: CorrelationID
    correlation_id: CorrelationID
    customer_id: Identifier
    tool: ToolName
    status: Literal["ok", "error", "denied", "timeout"]
    duration_ms: Annotated[int, Field(ge=0, le=3600000)]
    data: Annotated[FinancialSnapshot | Projection, Field(discriminator="kind")] | None
    error: ToolError | None

    @model_validator(mode="after")
    def matching_result(self):
        if self.status == "ok":
            if self.error is not None or self.data is None:
                raise ValueError("success requires data and no error")
            expected = "financial_snapshot" if self.tool == "data.snapshot" else "projection"
            if self.data.kind != expected:
                raise ValueError("tool/result mismatch")
            if self.data.customer_id != self.customer_id:
                raise ValueError("tool/customer mismatch")
        elif self.data is not None or self.error is None:
            raise ValueError("failure requires error and no financial data")
        return self


class AgentResponse(Contract):
    correlation_id: CorrelationID
    customer_id: Identifier
    mode: Literal["DEMO"]
    status: Literal["ok", "needs_data", "denied", "handoff", "error"]
    intent: Literal["project_cashflow", "unknown", "end_conversation", "handoff"]
    message: Annotated[str, Field(min_length=1, max_length=2000)]
    policy_decision_id: CorrelationID | None
    financial_result: Projection | None
    tool_results: Annotated[list[ToolResult], Field(max_length=10)]
    requires_human: bool

    @model_validator(mode="after")
    def response_integrity(self):
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
