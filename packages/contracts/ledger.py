"""Normalized competition data, independent from the DEMO snapshot protocol."""
from datetime import datetime
from typing import Annotated, Literal
from pydantic import Field, model_validator
from .base import Contract, Record, CorrelationID, Identifier, Money, Timestamp


class LedgerWindow(Record):
    from_time: Timestamp
    to_time: Timestamp

    @model_validator(mode="after")
    def valid_window(self):
        start = datetime.fromisoformat(self.from_time.replace("Z", "+00:00"))
        end = datetime.fromisoformat(self.to_time.replace("Z", "+00:00"))
        if not 0 < (end - start).total_seconds() <= 366 * 86400:
            raise ValueError("window must be positive and at most 366 days")
        return self


class LedgerReadRequest(Contract):
    correlation_id: CorrelationID
    customer_id: Identifier
    # Resolved by trusted Data Access identity mapping, never by an LLM.
    source_user_id: Annotated[str, Field(min_length=1, max_length=256)]
    from_time: Timestamp
    to_time: Timestamp

    @model_validator(mode="after")
    def bounded_window(self):
        start = datetime.fromisoformat(self.from_time.replace("Z", "+00:00"))
        end = datetime.fromisoformat(self.to_time.replace("Z", "+00:00"))
        if not 0 < (end - start).total_seconds() <= 366 * 86400:
            raise ValueError("ledger window must be positive and at most 366 days")
        return self


class CompetitionLedgerEntry(Record):
    occurred_at: Timestamp | None
    source_year_month: Annotated[int, Field(ge=100001, le=999912)] | None
    source_type: Annotated[str, Field(max_length=256)] | None
    description: Annotated[str, Field(max_length=4000)] | None
    amount_cents: Money | None
    balance_after_cents: Money | None
    macro_category: Annotated[str, Field(max_length=256)] | None
    micro_category: Annotated[str, Field(max_length=256)] | None
    installment_number: Annotated[int, Field(ge=0, le=2147483647)] | None
    installment_count: Annotated[int, Field(ge=0, le=2147483647)] | None
    amount_rounded: bool
    balance_rounded: bool

    @model_validator(mode="after")
    def source_integrity(self):
        if self.source_year_month is not None and not 1 <= self.source_year_month % 100 <= 12:
            raise ValueError("invalid source year/month")
        if self.installment_number is not None and self.installment_count is not None:
            if self.installment_number > self.installment_count:
                raise ValueError("installment number exceeds count")
        if self.amount_cents is None and self.amount_rounded:
            raise ValueError("missing amount cannot be rounded")
        if self.balance_after_cents is None and self.balance_rounded:
            raise ValueError("missing balance cannot be rounded")
        return self


class CompetitionLedger(Contract):
    kind: Literal["competition_ledger"]
    correlation_id: CorrelationID
    customer_id: Identifier
    provenance: Literal["COMPETITION_SYNTHETIC_BIGQUERY", "COMPETITION_SYNTHETIC_BIGQUERY_MOCK"]
    currency: Literal["BRL"]
    source_money_unit: Literal["major"]
    source_numeric_storage: Literal["FLOAT64_APPROXIMATE"]
    normalization: Literal["DECIMAL_STRING_HALF_UP_CENTS_V1"]
    from_time: Timestamp
    to_time: Timestamp
    entries: Annotated[list[CompetitionLedgerEntry], Field(max_length=1000)]
    # A complete query window is not a complete financial snapshot/account.
    complete_financial_context: Literal[False]

    @model_validator(mode="after")
    def window_integrity(self):
        start = datetime.fromisoformat(self.from_time.replace("Z", "+00:00"))
        end = datetime.fromisoformat(self.to_time.replace("Z", "+00:00"))
        if not 0 < (end - start).total_seconds() <= 366 * 86400:
            raise ValueError("invalid ledger result window")
        for entry in self.entries:
            if entry.occurred_at is not None:
                occurred = datetime.fromisoformat(entry.occurred_at.replace("Z", "+00:00"))
                if not start <= occurred < end:
                    raise ValueError("ledger entry outside window")
        return self


class LedgerCounts(Record):
    transaction_count: Annotated[int, Field(ge=0, le=1000)]
    balance_observation_count: Annotated[int, Field(ge=0, le=1000)]


MISSING_PROJECTION = ["confirmed_current_balance", "next_income_date", "next_income_amount", "future_commitments", "transaction_direction_semantics"]


class FinancialContext(Contract):
    kind: Literal["financial_context"]
    correlation_id: CorrelationID
    customer_id: Identifier
    status: Literal["INCOMPLETE_FINANCIAL_CONTEXT"]
    observed: CompetitionLedger
    calculated: LedgerCounts
    estimates: Annotated[list[str], Field(max_length=0)]
    inferences: Annotated[list[str], Field(max_length=0)]
    missing: Annotated[list[Literal["confirmed_current_balance", "next_income_date", "next_income_amount",
        "future_commitments", "transaction_direction_semantics", "transactions_in_window", "balance_after"]], Field(max_length=7)]

    @model_validator(mode="after")
    def evidence_integrity(self):
        if self.customer_id != self.observed.customer_id or self.correlation_id != self.observed.correlation_id:
            raise ValueError("observation identity mismatch")
        balances = sum(e.balance_after_cents is not None for e in self.observed.entries)
        if self.calculated.transaction_count != len(self.observed.entries) or self.calculated.balance_observation_count != balances:
            raise ValueError("counts lack observation evidence")
        expected = MISSING_PROJECTION + ([] if self.observed.entries else ["transactions_in_window"]) + ([] if balances else ["balance_after"])
        if self.missing != expected:
            raise ValueError("missing context cannot be concealed")
        return self


LEDGER_CONTRACTS = (LedgerReadRequest, CompetitionLedger, FinancialContext)
