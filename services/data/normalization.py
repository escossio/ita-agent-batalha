"""Only Data Access handles source FLOATs; no FLOAT crosses this boundary."""
from datetime import datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP, localcontext
import re
from packages.contracts.ledger import CompetitionLedgerEntry


class SourceDataError(Exception):
    pass


def decimal_source(value):
    if type(value) not in (str, int, float, Decimal):
        raise SourceDataError("INVALID_SOURCE_NUMBER")
    text = str(value)
    if len(text) > 128 or not re.fullmatch(r"[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?", text):
        raise SourceDataError("INVALID_SOURCE_NUMBER")
    try:
        number = Decimal(text)
    except InvalidOperation:
        raise SourceDataError("INVALID_SOURCE_NUMBER") from None
    if not number.is_finite() or abs(number.as_tuple().exponent) > 128 or abs(number) > Decimal("10000000000"):
        raise SourceDataError("SOURCE_NUMBER_OUT_OF_RANGE")
    return number


def money_to_cents(value):
    if value is None:
        return None, False
    with localcontext() as context:
        context.prec = 160
        scaled = decimal_source(value) * 100
        cents = scaled.to_integral_value(rounding=ROUND_HALF_UP)
        if abs(cents) > 10**12:
            raise SourceDataError("SOURCE_MONEY_OUT_OF_RANGE")
        return int(cents), scaled != cents


def integer_source(value):
    if value is None:
        return None
    number = decimal_source(value)
    if number != number.to_integral_value() or not 0 <= number <= 2147483647:
        raise SourceDataError("INVALID_SOURCE_INTEGER")
    return int(number)


def timestamp_source(value):
    if value is None:
        return None
    # BigQuery REST TIMESTAMP is decimal seconds since epoch. Avoid float arithmetic.
    with localcontext() as context:
        context.prec = 160
        micros = decimal_source(value) * 1_000_000
        if micros != micros.to_integral_value():
            raise SourceDataError("INVALID_TIMESTAMP_PRECISION")
        try:
            result = datetime(1970, 1, 1, tzinfo=timezone.utc) + timedelta(microseconds=int(micros))
        except (OverflowError, ValueError):
            raise SourceDataError("INVALID_TIMESTAMP") from None
        return result.isoformat().replace("+00:00", "Z")


def normalize_entry(row, source_user_id):
    if row.get("id_usuario") != source_user_id:
        raise SourceDataError("SOURCE_CUSTOMER_MISMATCH")
    amount, amount_rounded = money_to_cents(row["vlr"])
    balance, balance_rounded = money_to_cents(row["saldo_apos"])
    try:
        return CompetitionLedgerEntry(
            occurred_at=timestamp_source(row["anomesdia"]), source_year_month=integer_source(row["anomes"]),
            source_type=row["tipo"], description=row["descr"], amount_cents=amount, balance_after_cents=balance,
            macro_category=row["nom_cate_macro"], micro_category=row["nom_cate_micro"],
            installment_number=integer_source(row["parcela_atual"]), installment_count=integer_source(row["parcela_total"]),
            amount_rounded=amount_rounded, balance_rounded=balance_rounded)
    except SourceDataError:
        raise
    except (ValueError, TypeError, KeyError):
        raise SourceDataError("INVALID_SOURCE_ROW") from None
