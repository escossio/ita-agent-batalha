import unittest
from pydantic import ValidationError
from packages.contracts.ledger import CompetitionLedger, FinancialContext, MISSING_PROJECTION


class IncompleteContextContractTests(unittest.TestCase):
    def test_missing_evidence_cannot_be_replaced_with_estimates_or_invented_counts(self):
        ledger = CompetitionLedger(schema_version="1.0", kind="competition_ledger",
            correlation_id="00000000-0000-4000-8000-000000000001", customer_id="synthetic-customer",
            provenance="COMPETITION_SYNTHETIC_BIGQUERY", currency="BRL", source_money_unit="major",
            source_numeric_storage="FLOAT64_APPROXIMATE", normalization="DECIMAL_STRING_HALF_UP_CENTS_V1",
            from_time="2026-09-01T00:00:00Z", to_time="2026-10-01T00:00:00Z", entries=[], complete_financial_context=False)
        value = dict(schema_version="1.0", kind="financial_context", correlation_id=ledger.correlation_id,
            customer_id=ledger.customer_id, status="INCOMPLETE_FINANCIAL_CONTEXT", observed=ledger.model_dump(),
            calculated={"transaction_count": 0, "balance_observation_count": 0}, estimates=[], inferences=[],
            missing=MISSING_PROJECTION + ["transactions_in_window", "balance_after"])
        FinancialContext.model_validate(value)
        for mutation in ({"missing": []}, {"estimates": ["salary next month"]}, {"inferences": ["recurring salary"]},
                         {"status": "COMPLETE"}, {"customer_id": "other"},
                         {"calculated": {"transaction_count": 1, "balance_observation_count": 1}}):
            with self.subTest(mutation=mutation), self.assertRaises(ValidationError):
                FinancialContext.model_validate(value | mutation)
