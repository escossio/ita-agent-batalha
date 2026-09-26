"""Normalized competition data, independent from the DEMO snapshot protocol."""
from datetime import datetime
from typing import Annotated, Literal
from pydantic import Field, model_validator
from .models import Contract, Record, CorrelationID, Identifier, Money, Timestamp


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
    provenance: Literal["COMPETITION_SYNTHETIC_BIGQUERY"]
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


LEDGER_CONTRACTS = (LedgerReadRequest, CompetitionLedger)
