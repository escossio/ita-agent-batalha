"""Observed ledger is not a forecast; only deterministic counts are derived."""
from packages.contracts.base import Record, CorrelationID
from packages.contracts.ledger import CompetitionLedger, FinancialContext, MISSING_PROJECTION
from packages.runtime.audit import audit


class AssessmentInput(Record):
    correlation_id: CorrelationID
    ledger: CompetitionLedger


def assess(payload, correlation_id):
    value = AssessmentInput.model_validate(payload)
    if value.correlation_id != correlation_id or value.ledger.correlation_id != correlation_id:
        raise ValueError("correlation mismatch")
    audit(correlation_id, "finance", "calculation_started", "started")
    balances = sum(e.balance_after_cents is not None for e in value.ledger.entries)
    result = FinancialContext(schema_version="1.0", kind="financial_context", correlation_id=correlation_id,
        customer_id=value.ledger.customer_id, status="INCOMPLETE_FINANCIAL_CONTEXT", observed=value.ledger,
        calculated={"transaction_count": len(value.ledger.entries), "balance_observation_count": balances},
        estimates=[], inferences=[], missing=MISSING_PROJECTION + ([] if value.ledger.entries else ["transactions_in_window"])
        + ([] if balances else ["balance_after"]))
    audit(correlation_id, "finance", "calculation_completed", "ok")
    return 200, result.model_dump()
