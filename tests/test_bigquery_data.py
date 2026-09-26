import copy
from decimal import Decimal
import os
import unittest
from unittest.mock import patch
from pydantic import ValidationError
from packages.contracts.ledger import CompetitionLedger, CompetitionLedgerEntry, LedgerReadRequest
from packages.contracts.models import FinancialSnapshot, ToolRequest
from services.data.bigquery import BigQueryConfig, BigQueryLedgerReader, SOURCE_FIELDS
from services.data.normalization import SourceDataError, money_to_cents, integer_source, normalize_entry

CID = "00000000-0000-4000-8000-000000000001"


def request():
    return dict(schema_version="1.0", correlation_id=CID, customer_id="synthetic-customer",
                source_user_id="synthetic-source-user", from_time="2026-09-01T00:00:00Z", to_time="2026-10-01T00:00:00Z")


def source_row():
    return dict(id_usuario="synthetic-source-user", anomesdia="1788307200.000001", anomes="202609",
                tipo="UNVERIFIED_TYPE", descr="synthetic entry", vlr="-12.345", nom_cate_macro="synthetic macro",
                nom_cate_micro=None, saldo_apos="100.005", parcela_atual="2.0", parcela_total="3.0")


def config(**overrides):
    return BigQueryConfig(**(dict(project="demo-project", dataset="demo_dataset", table="demo_ledger",
                                 location="us-central1", currency="BRL", money_unit="major",
                                 maximum_bytes_billed=10000000) | overrides))


class Transport:
    def __init__(self):
        self.calls = []
        self.schema = {"fields": [{"name": name, "type": kind, "mode": "NULLABLE"} for name, kind in SOURCE_FIELDS]}
        self.metadata = dict(tableReference=dict(projectId="demo-project", datasetId="demo_dataset", tableId="demo_ledger"),
                             type="TABLE", location="us-central1", schema=copy.deepcopy(self.schema))
        self.result = dict(jobComplete=True, schema=copy.deepcopy(self.schema), totalRows="1",
                           rows=[{"f": [{"v": source_row()[name]} for name, _ in SOURCE_FIELDS]}])

    def request(self, method, url, payload, cid):
        self.calls.append((method, url, copy.deepcopy(payload), cid))
        return copy.deepcopy(self.metadata if method == "GET" else self.result)


class MoneyNormalizationTests(unittest.TestCase):
    def test_cents_are_decimal_half_up_signed_and_never_float(self):
        for source, expected in [(0, 0), (0.1 + 0.2, 30), (1.005, 101), (2.675, 268),
                                 (-1.005, -101), ("-0.005", -1), ("-0.0", 0), ("1.2345e2", 12345),
                                 (Decimal("9999999999.99"), 999999999999), ("10000000000", 10**12)]:
            with self.subTest(source=source):
                cents, _ = money_to_cents(source)
                self.assertEqual(cents, expected)
                self.assertIs(type(cents), int)
        self.assertEqual(money_to_cents(None), (None, False))
        self.assertEqual(money_to_cents("1.005"), (101, True))
        self.assertEqual(money_to_cents("1.00"), (100, False))
        # Normalize each source amount before aggregation, never sum binary floats.
        self.assertEqual(sum(money_to_cents(v)[0] for v in ["0.005", "0.005"]), 2)

    def test_invalid_or_nonfinite_monetary_source_is_rejected(self):
        for value in (True, False, float("nan"), float("inf"), "-Infinity", "NaN", "1,50", "", " 1",
                      "10000000000.01", "1e999999", "1e-999999", [], {}):
            with self.subTest(value=value), self.assertRaises(SourceDataError):
                money_to_cents(value)

    def test_installment_float_is_a_count_and_is_never_rounded(self):
        self.assertEqual(integer_source(2.0), 2)
        self.assertEqual(integer_source("0.0"), 0)
        self.assertIsNone(integer_source(None))
        for value in (2.5, "2.0000000001", -1, True, "NaN"):
            with self.subTest(value=value), self.assertRaises(SourceDataError):
                integer_source(value)

    def test_nullable_metadata_is_preserved_without_zero_or_financial_invention(self):
        row = {key: None for key in source_row()}
        row["id_usuario"] = "synthetic-source-user"
        entry = normalize_entry(row, "synthetic-source-user")
        self.assertIsNone(entry.amount_cents)
        self.assertIsNone(entry.balance_after_cents)
        self.assertIsNone(entry.occurred_at)
        self.assertIsNone(entry.installment_count)
        self.assertFalse(entry.amount_rounded)
        self.assertFalse(entry.balance_rounded)

    def test_amount_balance_and_microseconds_are_normalized_independently(self):
        entry = normalize_entry(source_row(), "synthetic-source-user")
        self.assertEqual((entry.amount_cents, entry.balance_after_cents), (-1235, 10001))
        self.assertEqual(entry.occurred_at, "2026-09-02T00:00:00.000001Z")
        self.assertEqual(entry.installment_number, 2)
        self.assertEqual(entry.source_type, "UNVERIFIED_TYPE")
        for values in ({"amount_cents": 10.0}, {"balance_after_cents": "10"}, {"installment_number": 2.0}):
            with self.assertRaises(ValidationError):
                CompetitionLedgerEntry.model_validate(entry.model_dump() | values)


class BigQueryReaderTests(unittest.TestCase):
    def setUp(self):
        self.transport = Transport()
        self.reader = BigQueryLedgerReader(config(), self.transport)

    def test_scoped_query_normalizes_both_money_fields_and_preserves_provenance(self):
        result = self.reader.read(request())
        self.assertEqual(result.entries[0].amount_cents, -1235)
        self.assertEqual(result.entries[0].balance_after_cents, 10001)
        self.assertEqual(result.provenance, "COMPETITION_SYNTHETIC_BIGQUERY")
        self.assertFalse(result.complete_financial_context)
        self.assertEqual(result.correlation_id, CID)
        self.assertEqual([call[0] for call in self.transport.calls], ["GET", "POST"])
        payload = self.transport.calls[1][2]
        self.assertNotIn(request()["source_user_id"], payload["query"])
        self.assertEqual(payload["queryParameters"][0]["parameterValue"]["value"], request()["source_user_id"])
        self.assertEqual(payload["maximumBytesBilled"], "10000000")
        self.assertEqual(payload["jobTimeoutMs"], "5000")
        self.assertIn("LIMIT 1001", payload["query"])
        self.assertEqual(payload["requestId"], CID)
        with self.assertRaises(ValidationError):
            FinancialSnapshot.model_validate(result.model_dump())
        with self.assertRaises(ValidationError):
            CompetitionLedger.model_validate(result.model_dump() | {"provenance": "DEMO_FIXTURE"})

    def test_prepared_adapter_does_not_create_an_unauthorized_tool(self):
        with self.assertRaises(ValidationError):
            ToolRequest.model_validate(dict(schema_version="1.0", request_id=CID, correlation_id=CID,
                                            customer_id="synthetic-customer", tool="data.ledger",
                                            arguments={"kind": "snapshot"}))
        result = self.reader.read(request()).model_dump()
        with self.assertRaises(ValidationError):
            CompetitionLedger.model_validate(result | {"to_time": result["from_time"]})

    def test_parameters_cannot_become_sql(self):
        value = request() | {"source_user_id": "x' OR TRUE --"}
        self.transport.result.update(rows=[], totalRows="0")
        self.reader.read(value)
        payload = self.transport.calls[-1][2]
        self.assertNotIn(value["source_user_id"], payload["query"])
        self.assertEqual(payload["queryParameters"][0]["parameterValue"]["value"], value["source_user_id"])

    def test_drift_wrong_source_or_location_prevents_query(self):
        for change in ("schema", "identity", "location", "view"):
            transport = Transport()
            if change == "schema":
                transport.metadata["schema"]["fields"][5]["type"] = "STRING"
            elif change == "identity":
                transport.metadata["tableReference"]["datasetId"] = "other"
            elif change == "location":
                transport.metadata["location"] = "EU"
            else:
                transport.metadata["type"] = "VIEW"
            with self.subTest(change=change), self.assertRaises(SourceDataError):
                BigQueryLedgerReader(config(), transport).read(request())
            self.assertEqual(len(transport.calls), 1)

    def test_incomplete_timeout_error_and_oversized_results_fail_closed(self):
        for change in ({"jobComplete": False}, {"errors": [{"message": "private"}]}, {"pageToken": "more"},
                       {"totalRows": "2"}, {"totalRows": "1001", "rows": self.transport.result["rows"] * 1001},
                       {"schema": {"fields": []}}):
            transport = Transport()
            transport.result.update(change)
            with self.subTest(change=list(change)), self.assertRaises(SourceDataError):
                BigQueryLedgerReader(config(), transport).read(request())

    def test_wrong_customer_missing_cell_invalid_money_and_outside_window_fail_closed(self):
        for field, bad in (("id_usuario", "another"), ("vlr", "NaN"), ("saldo_apos", "Infinity"),
                           ("anomesdia", "0"), ("parcela_atual", "1.5"), ("anomes", "202613")):
            transport = Transport()
            index = [name for name, _ in SOURCE_FIELDS].index(field)
            transport.result["rows"][0]["f"][index]["v"] = bad
            with self.subTest(field=field), self.assertRaises(SourceDataError):
                BigQueryLedgerReader(config(), transport).read(request())
        self.transport.result["rows"][0]["f"].pop()
        with self.assertRaises(SourceDataError):
            self.reader.read(request())

    def test_no_deduplication_without_source_transaction_id(self):
        self.transport.result["rows"] *= 2
        self.transport.result["totalRows"] = "2"
        self.assertEqual(len(self.reader.read(request()).entries), 2)

    def test_invalid_request_never_reaches_transport_or_falls_back(self):
        for change in ({"from_time": "2020-01-01T00:00:00Z"}, {"to_time": request()["from_time"]},
                       {"sql": "SELECT anything"}, {"source_user_id": ""}):
            with self.assertRaises(ValidationError):
                self.reader.read(request() | change)
        self.assertEqual(self.transport.calls, [])
        with patch.dict(os.environ, {}, clear=True), self.assertRaises(SourceDataError):
            BigQueryConfig.from_env()
        for change in ({"table": "table` WHERE TRUE --"}, {"currency": ""}, {"money_unit": "cents"},
                       {"maximum_bytes_billed": 0}, {"maximum_bytes_billed": True}):
            with self.assertRaises(SourceDataError):
                config(**change)
        with self.assertRaises(ValidationError):
            LedgerReadRequest.model_validate(request() | {"authorize": True})

    def test_dependency_error_is_sanitized_and_not_replaced_with_fixture(self):
        class Broken:
            def request(self, *args):
                raise RuntimeError("private project and credential detail")
        with self.assertRaisesRegex(SourceDataError, "^INVALID_BIGQUERY_RESULT$"):
            BigQueryLedgerReader(config(), Broken()).read(request())
