import copy
from datetime import datetime, timezone
import unittest
from pydantic import ValidationError
from services.policy.engine import PolicyEngine, matching_rules, request_digest
from services.policy.models import Facts, PolicyLimits
from packages.contracts.models import ToolRequest
from test_contracts import CID

NOW = datetime(2026, 9, 26, 12, tzinfo=timezone.utc)


def policy_input():
    return dict(correlation_id=CID, context=dict(schema_version="1.0", customer_id="demo-customer",
                mode="DEMO", consent_to_analysis=True, financial_level="stable", emotional_state="neutral",
                human_requested=False, provenance="DEMO_FIXTURE"), action="project_cashflow",
                request=dict(schema_version="1.0", request_id=CID, correlation_id=CID, customer_id="demo-customer",
                             tool="finance.project", arguments=dict(kind="projection", proposed_spend_cents=100)))


def products_input():
    value = policy_input()
    value.update(action="compare_products", request=None, requested_products=["credit"],
                 eligibility=dict(schema_version="1.0", customer_id="demo-customer", assessed_at=NOW.isoformat(),
                                  products=[dict(product="credit", status="eligible", source="DEMO_FIXTURE")]),
                 facts=dict(inadimplente=False, necessidade="liquidez", credito_elegivel=True,
                            capacidade_pagamento=True, necessidade_aderente=True, costs_verified=True))
    return value


class PolicyTests(unittest.TestCase):
    def setUp(self):
        self.engine = PolicyEngine()

    def decide(self, value):
        return self.engine.decide(value, NOW)

    def test_only_requested_tool_and_no_products_are_granted(self):
        decision = self.decide(policy_input())
        self.assertEqual(decision.authorized_tools, ["finance.project"])
        self.assertFalse(decision.allowed_products)
        self.assertFalse(decision.credit_allowed)

    def test_all_context_restrictions_fail_closed(self):
        for patch, expected in [({"consent_to_analysis": False}, "deny"),
                                ({"human_requested": True}, "handoff"),
                                ({"emotional_state": "crisis"}, "handoff"),
                                ({"emotional_state": "distressed"}, "handoff"),
                                ({"emotional_state": "unknown"}, "deny"),
                                ({"financial_level": "unknown"}, "deny")]:
            value = policy_input()
            value["context"].update(patch)
            with self.subTest(patch=patch):
                decision = self.decide(value)
                self.assertEqual(decision.outcome, expected)
                self.assertFalse(decision.authorized_tools)
                self.assertEqual(decision.max_options, 0)

    def test_person_safety_precedes_conversation(self):
        value = policy_input()
        value["context"]["emotional_state"] = "crisis"
        value["user_declined"] = True
        self.assertEqual(self.decide(value).reasons, ["PERSON_SAFETY"])

    def test_decline_never_schedules_or_reopens_authority(self):
        value = policy_input()
        value["user_declined"] = True
        decision = self.decide(value)
        self.assertEqual(decision.reasons, ["USER_DECLINED"])
        self.assertFalse(decision.authorized_tools)

    def test_proactive_requires_contact_consent(self):
        value = policy_input()
        value["proactive"] = True
        self.assertEqual(self.decide(value).outcome, "deny")
        value["context"]["contact_permission"] = True
        self.assertEqual(self.decide(value).outcome, "allow")

    def test_unknown_action_tool_and_forged_grants_rejected(self):
        for patch in ({"action": "move_money"}, {"allowed": True}, {"facts": {"ignore_policy": True}}):
            with self.subTest(patch=patch), self.assertRaises(ValidationError):
                self.decide(policy_input() | patch)
        value = policy_input()
        value["request"]["tool"] = "sql.execute"
        with self.assertRaises(ValidationError):
            self.decide(value)

    def test_request_and_eligibility_identity_binding(self):
        for key in ("customer_id", "correlation_id"):
            value = policy_input()
            value["request"][key] = "other" if key == "customer_id" else CID[:-1] + "2"
            with self.subTest(key=key), self.assertRaises(ValidationError):
                self.decide(value)
        value = products_input()
        value["eligibility"]["customer_id"] = "other"
        with self.assertRaises(ValidationError):
            self.decide(value)

    def test_server_kill_switch_and_tool_block(self):
        for limits in (PolicyLimits(service_enabled=False), PolicyLimits(blocked_tools=["finance.project"])):
            self.assertEqual(PolicyEngine(limits=limits).decide(policy_input(), NOW).outcome, "deny")

    def test_product_needs_all_proofs_not_just_eligibility(self):
        self.assertEqual(self.decide(products_input()).allowed_products, ["credit"])
        for field in ("necessidade_aderente", "capacidade_pagamento", "costs_verified", "credito_elegivel"):
            value = products_input()
            value["facts"].pop(field)
            with self.subTest(field=field):
                self.assertEqual(self.decide(value).outcome, "deny")
        for status in ("unknown", "ineligible"):
            value = products_input()
            value["eligibility"]["products"][0]["status"] = status
            self.assertEqual(self.decide(value).outcome, "deny")

    def test_stale_or_future_eligibility_is_not_permission(self):
        for timestamp in ("2026-09-24T12:00:00Z", "2026-09-27T12:00:00Z"):
            value = products_input()
            value["eligibility"]["assessed_at"] = timestamp
            self.assertEqual(self.decide(value).outcome, "deny")

    def test_financial_distress_blocks_credit_but_allows_requested_analysis(self):
        value = products_input()
        value["context"]["financial_level"] = "critical"
        self.assertEqual(self.decide(value).outcome, "deny")
        value = policy_input()
        value["context"]["financial_level"] = "critical"
        self.assertEqual(self.decide(value).authorized_tools, ["finance.project"])
        self.assertFalse(self.decide(value).credit_allowed)

    def test_explicit_product_block_cannot_be_overridden(self):
        decision = PolicyEngine(limits=PolicyLimits(blocked_products=["credit"])).decide(products_input(), NOW)
        self.assertEqual(decision.outcome, "deny")

    def test_delinquency_does_not_trigger_credit(self):
        value = products_input()
        value["facts"]["inadimplente"] = True
        self.assertEqual(self.decide(value).outcome, "deny")

    def test_missing_false_and_string_bool_are_different(self):
        self.assertEqual(matching_rules(Facts(), self.engine.rules), [])
        self.assertIn("R003", matching_rules(Facts(inadimplente=False, risco_saldo_negativo=True), self.engine.rules))
        with self.assertRaises(ValidationError):
            Facts(inadimplente="false")

    def test_decision_binds_arguments_with_short_expiry(self):
        value = policy_input()
        decision = self.decide(value)
        self.assertEqual((datetime.fromisoformat(decision.expires_at) - NOW).total_seconds(), 30)
        request = ToolRequest.model_validate(value["request"])
        self.assertEqual(decision.request_digest, request_digest(request))
        changed = copy.deepcopy(value)
        changed["request"]["arguments"]["proposed_spend_cents"] += 1
        self.assertNotEqual(decision.request_digest, self.decide(changed).request_digest)

    def test_tight_state_limits_product_options(self):
        value = products_input()
        value["context"]["financial_level"] = "tight"
        self.assertEqual(self.decide(value).max_options, 1)

    def test_http_boundary_preserves_correlation_and_denial(self):
        from services.policy.main import evaluate
        value = policy_input()
        value["context"]["consent_to_analysis"] = False
        status, result = evaluate(value, CID)
        self.assertEqual(status, 200)
        self.assertEqual(result["outcome"], "deny")
        with self.assertRaises(ValueError):
            evaluate(value, CID[:-1] + "2")

    def test_renegotiation_financing_consortium_and_investment_require_specific_evidence(self):
        cases = [
            ("renegotiation", dict(inadimplente=True, renegociacao_elegivel=True)),
            ("financing", dict(inadimplente=False, capacidade_pagamento=True, objetivo="aquisição",
                               urgencia="ALTA", financiamento_elegivel=True)),
            ("consortium", dict(inadimplente=False, capacidade_pagamento=True, objetivo="aquisição",
                               urgencia="BAIXA", consorcio_elegivel=True)),
            ("investment", dict(sobra_recorrente=True, reserva=False, profile_verified=True,
                                horizon_verified=True, liquidity_compatible=True)),
        ]
        for product, facts in cases:
            value = products_input()
            value["requested_products"] = [product]
            value["eligibility"]["products"][0]["product"] = product
            value["facts"] = dict(facts, necessidade_aderente=True, costs_verified=True)
            with self.subTest(product=product):
                self.assertEqual(self.decide(value).allowed_products, [product])
                value["facts"]["costs_verified"] = False
                self.assertEqual(self.decide(value).outcome, "deny")
