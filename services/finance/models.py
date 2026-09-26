from typing import Annotated, Literal
from pydantic import Field
from packages.contracts.models import (
    Amount, CorrelationID, FinancialSnapshot, HistoricalPeriod, Money, Record,
)


class ProjectionInput(Record):
    correlation_id: CorrelationID
    snapshot: FinancialSnapshot
    proposed_spend_cents: Amount


class Breakdown(Record):
    bills_cents: Amount
    installments_cents: Amount
    subscriptions_cents: Amount
    recurring_cents: Amount
    variable_cents: Amount
    confirmed_cents: Amount
    estimated_cents: Amount
    total_cents: Amount


class HistoryInput(Record):
    previous: HistoricalPeriod
    current: HistoricalPeriod


class HistoryComparison(Record):
    income_delta_cents: Money
    committed_delta_cents: Money
    variable_delta_cents: Money
    installment_delta_cents: Money
    surplus_delta_cents: Money
    negative_days_delta: Annotated[int, Field(ge=-31, le=31)]


class CostInput(Record):
    principal_cents: Amount
    periodic_rate_basis_points: Annotated[int, Field(ge=0, le=100000)] | None
    periods: Annotated[int, Field(ge=1, le=600)]
    regime: Literal["simple", "compound"]
    rate_verified: bool
    fees_cents: Amount


class CostResult(Record):
    principal_cents: Amount
    interest_cents: Amount
    fees_cents: Amount
    total_cents: Amount
    rounding: Literal["HALF_UP_CENTS"] = "HALF_UP_CENTS"
    scope: Literal["DEMO_SIMULATION_NOT_CET_OR_OFFER"] = "DEMO_SIMULATION_NOT_CET_OR_OFFER"
