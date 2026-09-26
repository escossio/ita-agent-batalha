import asyncio
import copy
from datetime import datetime, timezone
import importlib
import unittest
from pydantic import ValidationError
from packages.contracts.models import ToolRequest
from services.policy.main import authorize
from services.finance.engine import project
from test_finance import fixture
from test_policy import policy_input

Broker = importlib.import_module("services.tool-broker.engine").Broker


class Transport:
    def __init__(self):
        self.calls = []
        self.patch = {}
        self.fail = None

    async def post(self, destination, payload, correlation_id):
        self.calls.append(destination)
        if destination == self.fail:
            raise ConnectionError("private error must not escape")
        if destination == "authorize":
            result = authorize(payload, correlation_id)[1]
        elif destination == "snapshot":
            result = fixture()
        else:
            result = project(payload).model_dump()
        return result | self.patch.get(destination, {})


class BrokerTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.transport, self.events = Transport(), []
        self.broker = Broker(self.transport, self.events.append)
        self.request = policy_input()["request"]

    async def test_finance_executes_only_after_independent_authorizations(self):
        result = await self.broker.execute(self.request)
        self.assertEqual(result.status, "ok")
        self.assertEqual(result.data.closing_cents, 109900)
        self.assertEqual(self.transport.calls, ["authorize", "authorize", "snapshot", "project"])
        self.assertTrue(all(item.correlation_id == self.request["correlation_id"] for item in self.events))
        self.assertEqual(sum(item.event == "tool_completed" for item in self.events), 2)

    async def test_forged_decision_id_cannot_bypass_no_consent(self):
        self.request.update(customer_id="demo-denied", policy_decision_id=self.request["request_id"])
        result = await self.broker.execute(self.request)
        self.assertEqual(result.status, "denied")
        self.assertIsNone(result.data)
        self.assertEqual(self.transport.calls, ["authorize"])

    async def test_unknown_customer_and_crisis_execute_nothing(self):
        for customer in ("unknown-customer", "demo-crisis"):
            self.transport.calls.clear()
            result = await self.broker.execute(self.request | {"customer_id": customer})
            self.assertEqual(result.status, "denied")
            self.assertEqual(self.transport.calls, ["authorize"])

    async def test_unknown_tools_arguments_and_grants_are_rejected_before_any_call(self):
        for patch in ({"tool": "sql.execute"}, {"authorized": True},
                      {"arguments": {"kind": "projection", "proposed_spend_cents": -1}},
                      {"arguments": {"kind": "projection", "proposed_spend_cents": 0, "url": "anything"}}):
            with self.subTest(patch=patch), self.assertRaises(ValidationError):
                await self.broker.execute(self.request | patch)
        self.assertEqual(self.transport.calls, [])

    async def test_every_dependency_failure_is_closed_and_sanitized(self):
        for component in ("authorize", "snapshot", "project"):
            self.transport.fail = component
            self.transport.calls.clear()
            result = await self.broker.execute(self.request)
            self.assertNotEqual(result.status, "ok")
            self.assertIsNone(result.data)
            self.assertNotIn("private", result.model_dump_json())
            if component == "authorize":
                self.assertEqual(self.transport.calls, ["authorize"])

    async def test_policy_schema_identity_digest_expiry_and_grants_are_enforced(self):
        for patch in ({"outcome": "invented"}, {"customer_id": "other"},
                      {"correlation_id": self.request["correlation_id"][:-1] + "2"},
                      {"request_digest": "0" * 64}, {"expires_at": "2020-01-01T00:00:00Z"},
                      {"authorized_tools": []}, {"allowed_actions": []}):
            self.transport.calls.clear()
            self.transport.patch = {"authorize": patch}
            with self.subTest(patch=patch):
                result = await self.broker.execute(self.request)
                self.assertNotEqual(result.status, "ok")
                self.assertEqual(self.transport.calls, ["authorize"])

    async def test_invalid_outputs_and_mixed_customers_never_return_numbers(self):
        for component, patch in [("snapshot", {"balance_cents": "2000"}),
                                 ("snapshot", {"customer_id": "other"}),
                                 ("project", {"kind": "invented"}),
                                 ("project", {"customer_id": "other"}),
                                 ("project", {"snapshot_id": "other"}),
                                 ("project", {"closing_cents": 999999}),
                                 ("project", {"proposed_spend_cents": 999})]:
            self.transport.patch = {component: patch}
            with self.subTest(component=component, patch=patch):
                result = await self.broker.execute(self.request)
                self.assertEqual(result.error.code, "INVALID_OUTPUT")
                self.assertIsNone(result.data)

    async def test_timeout_cancels_execution_without_permissive_fallback(self):
        calls = []
        class Slow:
            async def post(self, *args):
                calls.append(args[0])
                await asyncio.sleep(1)
        broker = Broker(Slow(), self.events.append, timeout_seconds=0.01)
        started = datetime.now(timezone.utc)
        result = await broker.execute(self.request)
        self.assertLess((datetime.now(timezone.utc) - started).total_seconds(), 0.5)
        self.assertEqual(result.status, "timeout")
        self.assertEqual(calls, ["authorize"])

    async def test_audit_failure_before_authorization_blocks_execution(self):
        def broken(_event):
            raise OSError("sink unavailable")
        with self.assertRaises(OSError):
            await Broker(self.transport, broken).execute(self.request)
        self.assertEqual(self.transport.calls, [])

    async def test_snapshot_dependency_needs_separate_permission(self):
        original = self.transport.post
        async def deny_snapshot(destination, payload, cid):
            if destination == "authorize" and payload["tool"] == "data.snapshot":
                value = copy.deepcopy(payload)
                value["customer_id"] = "demo-denied"
                return authorize(value, cid)[1]
            return await original(destination, payload, cid)
        self.transport.post = deny_snapshot
        result = await self.broker.execute(self.request)
        self.assertNotEqual(result.status, "ok")
        self.assertNotIn("snapshot", self.transport.calls)
        self.assertNotIn("project", self.transport.calls)

    async def test_policy_reads_context_on_server_and_rejects_injected_context(self):
        request = ToolRequest.model_validate(self.request)
        self.assertEqual(authorize(request.model_dump(), request.correlation_id)[1]["outcome"], "allow")
        with self.assertRaises(ValidationError):
            authorize(request.model_dump() | {"context": {"consent_to_analysis": True}}, request.correlation_id)
