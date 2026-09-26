import copy
import unittest

from pydantic import ValidationError

from packages.contracts.models import (
    AgentResponse, AuditEvent, CONTRACTS, CustomerContext, Eligibility,
    FinancialSnapshot, PolicyDecision, ToolRequest, ToolResult,
)

CID = "00000000-0000-4000-8000-000000000001"


def snapshot():
    return dict(schema_version="1.0", kind="financial_snapshot", snapshot_id="demo-snapshot",
                customer_id="demo-customer", mode="DEMO", as_of="2026-09-01", currency="BRL",
                balance_cents=200000, next_income={"due_on": "2026-09-19", "amount_cents": 300000,
                "recurring_confirmed": True, "certainty": "confirmed"}, commitments=[],
                history=None, data_complete=True, provenance="DEMO_FIXTURE")


def denial():
    return dict(schema_version="1.0", decision_id=CID, correlation_id=CID,
                customer_id="demo-customer", request_digest="0" * 64, outcome="deny",
                allowed_actions=[], blocked_actions=["project_cashflow"], allowed_products=[],
                blocked_products=["credit"], authorized_tools=[], credit_allowed=False,
                max_options=0, requires_human=False, language_constraints=["no_invented_numbers"],
                reasons=["DEFAULT_DENY"], policy_version="1.0", expires_at="2026-09-01T12:00:00Z")


class ContractTests(unittest.TestCase):
    def test_all_eight_schemas_reject_extra_properties(self):
        self.assertEqual(len(CONTRACTS), 8)
        for contract in CONTRACTS:
            schema = contract.model_json_schema()
            self.assertIs(schema["additionalProperties"], False)
            self.assertIn("schema_version", schema["required"])
            self.assertEqual(schema["properties"]["schema_version"]["const"], "1.0")

    def test_customer_context_requires_provenance_and_consent(self):
        valid = dict(schema_version="1.0", customer_id="demo-customer", mode="DEMO",
                     consent_to_analysis=True, financial_level="stable", emotional_state="neutral",
                     human_requested=False, provenance="DEMO_FIXTURE")
        self.assertFalse(CustomerContext.model_validate(valid).contact_permission)
        for field in ("consent_to_analysis", "provenance", "financial_level"):
            value = copy.deepcopy(valid)
            value.pop(field)
            with self.subTest(field=field), self.assertRaises(ValidationError):
                CustomerContext.model_validate(value)

    def test_money_is_integer_not_bool_float_or_string(self):
        for amount in (True, 1.1, "100", 10**13, None):
            value = snapshot()
            value["balance_cents"] = amount
            with self.subTest(amount=amount), self.assertRaises(ValidationError):
                FinancialSnapshot.model_validate(value)

    def test_incomplete_snapshot_is_explicit_not_invented(self):
        value = snapshot()
        value["next_income"] = None
        value["data_complete"] = False
        self.assertIsNone(FinancialSnapshot.model_validate(value).next_income)
        value.pop("next_income")
        with self.assertRaises(ValidationError):
            FinancialSnapshot.model_validate(value)

    def test_invalid_dates_versions_currency_and_authority_fields(self):
        for patch in ({"as_of": "2026-02-30"}, {"schema_version": "2.0"},
                      {"currency": "USD"}, {"authorize_all": True}):
            with self.subTest(patch=patch), self.assertRaises(ValidationError):
                FinancialSnapshot.model_validate(snapshot() | patch)
        value = snapshot()
        value["next_income"]["due_on"] = value["as_of"]
        with self.assertRaises(ValidationError):
            FinancialSnapshot.model_validate(value)

    def test_duplicate_commitments_and_invalid_installments(self):
        item = dict(entry_id="demo-entry", due_on="2026-09-02", amount_cents=10,
                    category="installment", certainty="confirmed", installment_number=2,
                    installment_count=1)
        for commitments in ([item], [dict(item, installment_count=3)] * 2):
            with self.subTest(commitments=commitments), self.assertRaises(ValidationError):
                FinancialSnapshot.model_validate(snapshot() | {"commitments": commitments})

    def test_eligibility_is_explicit_and_timestamp_is_utc(self):
        value = dict(schema_version="1.0", customer_id="demo-customer",
                     assessed_at="2026-09-01T12:00:00Z", products=[
                         dict(product="credit", status="unknown", source="DEMO_FIXTURE")])
        Eligibility.model_validate(value)
        for patch in ({"products": value["products"] * 2}, {"assessed_at": "2026-09-01T12:00:00"}):
            with self.subTest(patch=patch), self.assertRaises(ValidationError):
                Eligibility.model_validate(value | patch)

    def test_deny_cannot_contain_grants(self):
        PolicyDecision.model_validate(denial())
        for patch in ({"authorized_tools": ["finance.project"]}, {"allowed_actions": ["read_snapshot"]},
                      {"max_options": 1}, {"credit_allowed": True}, {"outcome": "handoff"}):
            with self.subTest(patch=patch), self.assertRaises(ValidationError):
                PolicyDecision.model_validate(denial() | patch)

    def test_tool_protocol_is_typed_and_allowlisted(self):
        value = dict(schema_version="1.0", request_id=CID, correlation_id=CID,
                     customer_id="demo-customer", tool="finance.project",
                     arguments={"kind": "projection", "proposed_spend_cents": 80000})
        ToolRequest.model_validate(value)
        for patch in ({"tool": "sql.execute"}, {"arguments": {"kind": "snapshot"}},
                      {"arguments": {"kind": "projection", "proposed_spend_cents": -1}},
                      {"arguments": {"kind": "projection", "proposed_spend_cents": 10, "sql": "anything"}}):
            with self.subTest(patch=patch), self.assertRaises(ValidationError):
                ToolRequest.model_validate(value | patch)

    def test_tool_failures_cannot_contain_financial_data(self):
        value = dict(schema_version="1.0", request_id=CID, correlation_id=CID,
                     customer_id="demo-customer", tool="data.snapshot", status="error", duration_ms=1, data=None,
                     error={"code": "DEPENDENCY_UNAVAILABLE", "retryable": True})
        ToolResult.model_validate(value)
        for patch in ({"data": snapshot()}, {"status": "ok"}, {"error": None}):
            with self.subTest(patch=patch), self.assertRaises(ValidationError):
                ToolResult.model_validate(value | patch)

    def test_agent_response_requires_matching_tool_evidence(self):
        value = dict(schema_version="1.0", correlation_id=CID, customer_id="demo-customer",
                     mode="DEMO", status="needs_data", intent="project_cashflow",
                     message="Falta informação para calcular.", policy_decision_id=None,
                     financial_result=None, tool_results=[], requires_human=False)
        AgentResponse.model_validate(value)
        with self.assertRaises(ValidationError):
            AgentResponse.model_validate(value | {"status": "handoff"})
        result = dict(kind="projection", customer_id="demo-customer", currency="BRL", snapshot_id="demo-snapshot",
                      as_of="2026-09-01", until="2026-09-19", opening_cents=200000,
                      commitments_cents=0, estimates_cents=0, proposed_spend_cents=0,
                      base_closing_cents=200000, closing_cents=200000, lowest_balance_cents=200000,
                      uncertain=False, warnings=[])
        with self.assertRaises(ValidationError):
            AgentResponse.model_validate(value | {"status": "ok", "financial_result": result})

    def test_audit_event_rejects_raw_private_payload(self):
        value = dict(schema_version="1.0", event_id=CID, correlation_id=CID,
                     occurred_at="2026-09-01T12:00:00Z", component="policy",
                     event="policy_decided", status="denied", reason="NO_CONSENT")
        AuditEvent.model_validate(value)
        with self.assertRaises(ValidationError):
            AuditEvent.model_validate(value | {"raw_request": "private conversation"})
