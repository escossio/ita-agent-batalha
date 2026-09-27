import copy
from datetime import datetime, timedelta, timezone
import hashlib
import importlib
import io
import json
import os
from pathlib import Path
import secrets
import tempfile
import time
import unittest
from unittest.mock import patch
from google.auth.exceptions import DefaultCredentialsError
from requests.exceptions import Timeout
from packages.contracts.models import ToolRequest
from packages.runtime.http_client import RemoteFailure
from packages.runtime.server import request_headers
from packages.runtime.service_auth import BrokerAuthenticator, broker_headers, sign_identity
from services.agent.orchestrator import Orchestrator
from services.agent.providers import MockProvider
from services.api.main import chat_async
from services.data import main as data_main
from services.data.bigquery import BigQueryTransport
from services.data.normalization import SourceDataError
from services.finance.ledger import assess
from services.policy.main import authorize
from test_bigquery_data import source_row, CID

Broker = importlib.import_module("services.tool-broker.engine").Broker


class DataPolicy:
    def _post(self, destination, payload, cid):
        return authorize(payload, cid)[1]


class Ports:
    def __init__(self):
        self.calls = []
        self.broker = Broker(self, lambda event: None)

    async def post(self, destination, payload, cid):
        self.calls.append((destination, copy.deepcopy(payload)))
        if destination == "authorize":
            return authorize(payload, cid)[1]
        if destination == "execute":
            return (await self.broker.execute(payload)).model_dump()
        if destination == "respond":
            return (await Orchestrator(MockProvider(), self, lambda event: None).run(payload)).model_dump()
        if destination == "ledger":
            status, result = data_main.ledger(payload, cid)
        elif destination == "assess":
            status, result = assess(payload, cid)
        else:
            raise AssertionError("unexpected route")
        if status != 200:
            raise RemoteFailure(result["error"])
        return result


class CompetitionRuntimeTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.session = secrets.token_urlsafe(40)
        self.registry = {"bindings": [{"context": dict(schema_version="1.0", customer_id="synthetic-customer", mode="COMPETITION",
            consent_to_analysis=True, financial_level="unknown", emotional_state="neutral", human_requested=False,
            provenance="VERIFIED_RUNTIME_IDENTITY"), "source_user_id": "synthetic-source-user",
            "session_hash": hashlib.sha256(self.session.encode()).hexdigest(),
            "expires_at": (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat(), "max_window_days": 366}]}
        (self.root / "registry.json").write_text(json.dumps(self.registry))
        (self.root / "rows.json").write_text(json.dumps([source_row()]))
        for name in ("identity-key", "broker-key"):
            (self.root / name).write_bytes(secrets.token_bytes(64))
        env = dict(ITA_RUNTIME_MODE="competition", ITA_DATA_PROVIDER="bigquery_mock", GOOGLE_CLOUD_PROJECT="demo-project",
            ITA_BIGQUERY_DATASET="demo_dataset", ITA_BIGQUERY_TABLE="demo_ledger", ITA_BIGQUERY_LOCATION="us-central1",
            ITA_BIGQUERY_CURRENCY="BRL", ITA_BIGQUERY_MONEY_UNIT="major", ITA_BIGQUERY_MAX_BYTES_BILLED="10000000",
            ITA_IDENTITY_REGISTRY_FILE=str(self.root / "registry.json"), ITA_BIGQUERY_MOCK_ROWS_FILE=str(self.root / "rows.json"),
            ITA_IDENTITY_KEY_FILE=str(self.root / "identity-key"), ITA_BROKER_DATA_KEY_FILE=str(self.root / "broker-key"))
        self.env_patch = patch.dict(os.environ, env)
        self.env_patch.start()
        self.addCleanup(self.env_patch.stop)
        for target in ("services.data.main.audit", "services.finance.ledger.audit", "services.api.main.audit"):
            mocked = patch(target)
            mocked.start()
            self.addCleanup(mocked.stop)
        policy_patch = patch("services.data.main.HttpTransport", DataPolicy)
        policy_patch.start()
        self.addCleanup(policy_patch.stop)
        self.header_token = request_headers.set({"Authorization": "Bearer " + self.session})
        self.ports = Ports()
        self.payload = dict(utterance="Até o próximo salário dá?", amount_brl="500,00", consent_to_analysis=True,
                            window=dict(from_time="2026-09-01T00:00:00Z", to_time="2026-10-01T00:00:00Z"))

    async def asyncTearDown(self):
        request_headers.reset(self.header_token)

    async def invoke(self, patch_value=None):
        return await chat_async(self.payload | (patch_value or {}), CID, self.ports)

    async def test_valid_customer_traverses_all_boundaries_without_future_inference(self):
        result = await self.invoke()
        self.assertEqual(result.status, "needs_data")
        self.assertEqual(result.mode, "COMPETITION")
        self.assertIsNone(result.financial_result)
        context = result.financial_context
        self.assertEqual(context.status, "INCOMPLETE_FINANCIAL_CONTEXT")
        self.assertEqual(context.observed.entries[0].amount_cents, -1235)
        self.assertEqual(context.observed.entries[0].balance_after_cents, 10001)
        self.assertEqual(context.observed.entries[0].installment_number, 2)
        self.assertEqual(context.observed.entries[0].macro_category, "synthetic macro")
        self.assertEqual(context.estimates, [])
        self.assertEqual(context.inferences, [])
        self.assertIn("next_income_date", context.missing)
        self.assertIn("future_commitments", context.missing)
        self.assertEqual(context.calculated.transaction_count, 1)
        self.assertIn("MOCK", context.observed.provenance)
        self.assertEqual([name for name, _ in self.ports.calls], ["respond", "authorize", "execute", "authorize", "authorize", "ledger", "assess"])

    async def test_null_fields_missing_balance_and_amount_remain_missing(self):
        row = source_row() | {"saldo_apos": None, "vlr": None, "parcela_atual": None, "parcela_total": None,
                              "descr": None, "nom_cate_macro": None, "nom_cate_micro": None}
        (self.root / "rows.json").write_text(json.dumps([row]))
        result = await self.invoke()
        context = result.financial_context
        self.assertIsNone(context.observed.entries[0].amount_cents)
        self.assertIsNone(context.observed.entries[0].balance_after_cents)
        self.assertEqual(context.calculated.balance_observation_count, 0)
        self.assertIn("balance_after", context.missing)
        self.assertIsNone(result.financial_result)

    async def test_empty_window_and_mapped_customer_absent_from_source_do_not_invent_existence(self):
        for rows in ([], [source_row() | {"id_usuario": "different-customer"}], [source_row() | {"anomesdia": "0"}]):
            (self.root / "rows.json").write_text(json.dumps(rows))
            result = await self.invoke()
            self.assertEqual(result.financial_context.observed.entries, [])
            self.assertIn("transactions_in_window", result.financial_context.missing)
            self.assertIsNone(result.financial_result)

    async def test_invalid_session_or_unmapped_customer_never_reaches_agent(self):
        request_headers.set({"Authorization": "Bearer " + secrets.token_urlsafe(40)})
        with self.assertRaises(PermissionError):
            await self.invoke()
        self.assertEqual(self.ports.calls, [])

    async def test_window_required_and_maximum_window_enforced(self):
        result = await self.invoke({"window": None})
        self.assertEqual(result.status, "needs_data")
        self.assertNotIn("execute", [name for name, _ in self.ports.calls])
        result = await self.invoke({"window": dict(from_time="2025-09-30T00:00:00Z", to_time="2026-10-01T00:00:00Z")})
        self.assertIsNotNone(result.financial_context)
        with self.assertRaises(ValueError):
            await self.invoke({"window": dict(from_time="2025-09-29T00:00:00Z", to_time="2026-10-01T00:00:00Z")})

    async def test_policy_binds_client_window_spend_session_and_expiry(self):
        await self.invoke()
        valid = next(payload for name, payload in self.ports.calls if name == "execute")
        for change in ({"customer_id": "other"}, {"identity_proof": None},
                       {"arguments": dict(kind="projection", proposed_spend_cents=99, ledger_window=self.payload["window"])}):
            value = ToolRequest.model_validate(valid | change)
            self.assertNotEqual(authorize(value.model_dump(), CID)[1]["outcome"], "allow")
        forged = copy.deepcopy(valid)
        forged["arguments"]["ledger_window"]["from_time"] = "2026-09-02T00:00:00Z"
        self.assertNotEqual(authorize(forged, CID)[1]["outcome"], "allow")
        self.registry["bindings"][0]["session_hash"] = "0" * 64
        (self.root / "registry.json").write_text(json.dumps(self.registry))
        self.assertNotEqual(authorize(valid, CID)[1]["outcome"], "allow")
        other_cid = "00000000-0000-4000-8000-000000000002"
        self.assertNotEqual(authorize(valid | {"correlation_id": other_cid}, other_cid)[1]["outcome"], "allow")

    async def test_direct_data_requires_broker_signature_rejects_replay_and_reauthorizes(self):
        await self.invoke()
        payload = next(p for name, p in self.ports.calls if name == "ledger")
        auth = BrokerAuthenticator()
        with self.assertRaises(PermissionError):
            auth(payload, CID, {}, "/v1/ledger")
        headers = broker_headers("/v1/ledger", payload, CID)
        auth(payload, CID, headers, "/v1/ledger")
        with self.assertRaises(PermissionError):
            auth(payload, CID, headers, "/v1/ledger")
        with self.assertRaises(PermissionError):
            BrokerAuthenticator()(payload | {"customer_id": "other"}, CID, headers, "/v1/ledger")
        with self.assertRaises(PermissionError):
            data_main.ledger(payload | {"identity_proof": None}, CID)
        self.registry["bindings"][0]["context"]["consent_to_analysis"] = False
        (self.root / "registry.json").write_text(json.dumps(self.registry))
        with self.assertRaises(PermissionError):
            data_main.ledger(payload, CID)

    async def test_consent_restriction_and_expired_assertion_cannot_be_overridden(self):
        result = await self.invoke({"consent_to_analysis": False})
        self.assertEqual(result.status, "denied")
        self.assertNotIn("ledger", [name for name, _ in self.ports.calls])
        proof = sign_identity(dict(customer_id="synthetic-customer", correlation_id=CID, window=self.payload["window"],
            proposed_spend_cents=50000, expires=int(time.time()) - 1, session_hash=self.registry["bindings"][0]["session_hash"]))
        value = dict(schema_version="1.0", request_id=CID, correlation_id=CID, customer_id="synthetic-customer", tool="data.ledger",
                     identity_proof=proof, arguments=dict(kind="ledger", window=self.payload["window"]))
        self.assertNotEqual(authorize(value, CID)[1]["outcome"], "allow")

    async def test_bigquery_failures_never_produce_context_or_projection(self):
        for code, expected in (("BIGQUERY_AUTHENTICATION_FAILED", "SOURCE_AUTHENTICATION_FAILED"),
                               ("BIGQUERY_SCHEMA_DRIFT", "SOURCE_SCHEMA_MISMATCH"), ("BIGQUERY_QUERY_TIMEOUT", "TIMEOUT"),
                               ("BIGQUERY_LOCATION_MISMATCH", "SOURCE_REGION_MISMATCH"), ("BIGQUERY_SOURCE_NOT_FOUND", "SOURCE_NOT_FOUND")):
            with patch("services.data.main.configured_reader") as reader:
                reader.return_value.read.side_effect = SourceDataError(code)
                result = await self.invoke()
            self.assertEqual(result.status, "error")
            self.assertIsNone(result.financial_result)
            self.assertIsNone(result.financial_context)
            self.assertEqual(result.tool_results[0].error.code, expected)


class BigQueryTransportFailureTests(unittest.TestCase):
    def test_adc_authentication_and_timeout_are_sanitized_without_network(self):
        for error, code in ((DefaultCredentialsError("private"), "BIGQUERY_AUTHENTICATION_FAILED"),
                            (Timeout("private"), "BIGQUERY_QUERY_TIMEOUT")):
            with patch("google.auth.default", side_effect=error), self.assertRaisesRegex(SourceDataError, code):
                BigQueryTransport().request("GET", "https://bigquery.googleapis.com/", None, CID)

    def test_dataset_or_table_not_found_and_permission_error_are_distinct(self):
        class Response:
            status_code = 404
            raw = io.BytesIO(b"private")
            def __enter__(self):
                return self
            def __exit__(self, *args):
                pass
        for status, code in ((404, "BIGQUERY_SOURCE_NOT_FOUND"), (403, "BIGQUERY_AUTHENTICATION_FAILED")):
            response = Response()
            response.status_code = status
            with patch("google.auth.default", return_value=(object(), "unused")), patch("google.auth.transport.requests.AuthorizedSession") as session:
                session.return_value.__enter__.return_value.request.return_value = response
                with self.assertRaisesRegex(SourceDataError, code):
                    BigQueryTransport().request("GET", "https://bigquery.googleapis.com/", None, CID)
