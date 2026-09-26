"""Cálculos determinísticos; não consulta LLM, Policy, rede ou banco."""
from decimal import Decimal, ROUND_HALF_UP, localcontext
from packages.contracts.models import FinancialSnapshot, Projection
from .models import Breakdown, CostInput, CostResult, HistoryComparison, HistoryInput, ProjectionInput


class MissingData(ValueError):
    pass


def breakdown(snapshot: FinancialSnapshot) -> Breakdown:
    snapshot = FinancialSnapshot.model_validate(snapshot.model_dump())
    if snapshot.next_income is None or not snapshot.data_complete:
        raise MissingData("complete snapshot and next income required")
    items = [item for item in snapshot.commitments if item.due_on < snapshot.next_income.due_on]
    categories = {name: sum(item.amount_cents for item in items if item.category == name)
                  for name in ("bill", "installment", "subscription", "recurring", "variable")}
    return Breakdown(bills_cents=categories["bill"], installments_cents=categories["installment"],
                     subscriptions_cents=categories["subscription"], recurring_cents=categories["recurring"],
                     variable_cents=categories["variable"],
                     confirmed_cents=sum(item.amount_cents for item in items if item.certainty == "confirmed"),
                     estimated_cents=sum(item.amount_cents for item in items if item.certainty == "estimated"),
                     total_cents=sum(item.amount_cents for item in items))


def project(payload: dict) -> Projection:
    value = ProjectionInput.model_validate(payload)
    snapshot = value.snapshot
    totals = breakdown(snapshot)
    # Incoming salary itself is outside the horizon (ADR-0003).
    base = snapshot.balance_cents - totals.total_cents
    closing = base - value.proposed_spend_cents
    uncertain = any(item.certainty == "estimated" for item in snapshot.commitments
                    if item.due_on < snapshot.next_income.due_on) or snapshot.next_income.certainty == "estimated"
    return Projection(kind="projection", customer_id=snapshot.customer_id, currency="BRL",
                      snapshot_id=snapshot.snapshot_id, as_of=snapshot.as_of, until=snapshot.next_income.due_on,
                      opening_cents=snapshot.balance_cents, commitments_cents=totals.confirmed_cents,
                      estimates_cents=totals.estimated_cents, proposed_spend_cents=value.proposed_spend_cents,
                      base_closing_cents=base, closing_cents=closing,
                      lowest_balance_cents=min(snapshot.balance_cents - value.proposed_spend_cents, closing),
                      uncertain=uncertain, warnings=["UNCERTAIN_DATA"] if uncertain else [])


def compare_history(payload: dict) -> HistoryComparison:
    value = HistoryInput.model_validate(payload)
    previous, current = value.previous, value.current
    if not previous.complete or not current.complete:
        raise MissingData("complete historical periods required")
    if previous.month >= current.month:
        raise ValueError("history must be chronological")
    # committed includes bills, installments, subscriptions and recurring; variable is disjoint.
    old_surplus = previous.income_cents - previous.committed_cents - previous.variable_cents
    new_surplus = current.income_cents - current.committed_cents - current.variable_cents
    return HistoryComparison(income_delta_cents=current.income_cents - previous.income_cents,
                             committed_delta_cents=current.committed_cents - previous.committed_cents,
                             variable_delta_cents=current.variable_cents - previous.variable_cents,
                             installment_delta_cents=current.installment_cents - previous.installment_cents,
                             surplus_delta_cents=new_surplus - old_surplus,
                             negative_days_delta=current.negative_days - previous.negative_days)


def costs(payload: dict) -> CostResult:
    value = CostInput.model_validate(payload)
    if not value.rate_verified or value.periodic_rate_basis_points is None:
        raise MissingData("verified rate required")
    with localcontext() as context:
        context.prec = 80
        principal = Decimal(value.principal_cents)
        rate = Decimal(value.periodic_rate_basis_points) / Decimal(10000)
        factor = (1 + rate * value.periods if value.regime == "simple" else (1 + rate) ** value.periods)
        # Refuse out-of-contract results before converting/quantizing enormous amounts.
        if principal * factor + value.fees_cents > 10**12:
            raise ValueError("cost exceeds money bounds")
        interest = int((principal * (factor - 1)).quantize(Decimal(1), rounding=ROUND_HALF_UP))
    return CostResult(principal_cents=value.principal_cents, interest_cents=interest,
                      fees_cents=value.fees_cents, total_cents=value.principal_cents + interest + value.fees_cents)
