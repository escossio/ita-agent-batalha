from typing import Annotated, Literal
from pydantic import Field, model_validator
from packages.contracts.ledger import LedgerWindow
from packages.contracts.models import Amount, Contract, CorrelationID, CustomerContext, Record


class AgentInput(Contract):
    window: LedgerWindow | None = None
    identity_proof: Annotated[str, Field(max_length=4096)] | None = None
    correlation_id: CorrelationID
    context: CustomerContext
    utterance: Annotated[str, Field(min_length=1, max_length=2000)]
    proposed_spend_cents: Amount = 0


class ModelPlan(Record):
    intent: Literal["project_cashflow", "unknown", "end_conversation", "handoff"]
    tool: Literal["finance.project", "none"]

    @model_validator(mode="after")
    def intent_tool(self):
        if (self.intent == "project_cashflow") != (self.tool == "finance.project"):
            raise ValueError("intent/tool mismatch")
        return self


class NarrativePlan(Record):
    introduction: Literal["direct", "supportive"]
    closing: Literal["customer_choice"]
