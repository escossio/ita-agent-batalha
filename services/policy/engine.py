"""Policy 1.0: dados estruturados, default deny, nenhum prompt ou LLM."""
from datetime import datetime, timedelta, timezone
import hashlib
import json
from pathlib import Path
from uuid import uuid4

from packages.contracts.models import PolicyDecision, ToolRequest
from .models import Facts, PolicyInput, PolicyLimits

PRODUCTS = ["credit", "renegotiation", "financing", "consortium", "investment"]
ACTIONS = ["read_snapshot", "project_cashflow", "compare_products", "end_conversation", "handoff"]


def request_digest(request: ToolRequest) -> str:
    data = request.model_dump(exclude={"policy_decision_id"})
    return hashlib.sha256(json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()).hexdigest()


def matching_rules(facts: Facts, rules: list[dict]) -> list[str]:
    values = facts.model_dump()
    return [rule["id"] for rule in rules if all(
        predicate["operator"] == "eq" and values.get(predicate["field"]) is not None
        and type(values[predicate["field"]]) is type(predicate["value"])
        and values[predicate["field"]] == predicate["value"] for predicate in rule["all"]
    )]


class PolicyEngine:
    def __init__(self, rules_path: Path = Path("config/rules.json"), limits: PolicyLimits | None = None):
        self.rules = json.loads(rules_path.read_text())["rules"]
        self.limits = PolicyLimits.model_validate((limits or PolicyLimits()).model_dump())

    def decide(self, payload: dict, now: datetime | None = None) -> PolicyDecision:
        value = PolicyInput.model_validate(payload)
        now = now or datetime.now(timezone.utc)
        if now.tzinfo is None or now.utcoffset().total_seconds() != 0:
            raise ValueError("policy clock must be UTC")
        context, facts = value.context, value.facts
        digest = request_digest(value.request) if value.request else hashlib.sha256(
            value.model_dump_json().encode()).hexdigest()
        result = dict(schema_version="1.0", decision_id=str(uuid4()), correlation_id=value.correlation_id,
                      customer_id=context.customer_id, request_digest=digest, outcome="deny",
                      allowed_actions=[], blocked_actions=list(ACTIONS), allowed_products=[],
                      blocked_products=list(PRODUCTS), authorized_tools=[], credit_allowed=False,
                      max_options=0, requires_human=False, language_constraints=[
                          "no_judgment", "no_invented_numbers", "no_pressure", "no_product_offer"],
                      reasons=["DEFAULT_DENY"], policy_version="1.0",
                      expires_at=(now + timedelta(seconds=30)).isoformat())

        def finish(reason, handoff=False):
            result["reasons"] = [reason]
            if handoff:
                result.update(outcome="handoff", requires_human=True)
            return PolicyDecision.model_validate(result)

        # ADR-0002: higher-priority restrictions before any grant.
        if context.emotional_state == "crisis":
            return finish("PERSON_SAFETY", True)
        if not self.limits.service_enabled:
            return finish("DEFAULT_DENY")
        if context.human_requested or value.action == "handoff":
            return finish("HUMAN_REQUESTED", True)
        if value.user_declined:
            return finish("USER_DECLINED")
        if value.action == "end_conversation":
            result.update(outcome="allow", allowed_actions=[value.action],
                          blocked_actions=[action for action in ACTIONS if action != value.action])
            return finish("ALLOWED")
        if not context.consent_to_analysis or (value.proactive and not context.contact_permission):
            return finish("NO_CONSENT")
        if context.emotional_state == "unknown" or context.financial_level == "unknown":
            return finish("UNKNOWN_CONTEXT")
        if context.emotional_state == "distressed":
            return finish("PERSON_SAFETY", True)
        if value.request is not None:
            if value.request.tool in self.limits.blocked_tools:
                return finish("TOOL_NOT_ALLOWED")
            result.update(outcome="allow", allowed_actions=[value.action],
                          blocked_actions=[action for action in ACTIONS if action != value.action],
                          authorized_tools=[value.request.tool])
            if context.financial_level == "critical":
                result["language_constraints"].append("signal_uncertainty")
            return finish("ALLOWED")
        if value.action != "compare_products" or not value.requested_products:
            return finish("DEFAULT_DENY")
        if context.financial_level == "critical":
            return finish("FINANCIAL_DISTRESS")
        if value.eligibility is None:
            return finish("INELIGIBLE")
        age = (now - datetime.fromisoformat(value.eligibility.assessed_at.replace("Z", "+00:00"))).total_seconds()
        if not 0 <= age <= self.limits.eligibility_max_age_seconds:
            return finish("INELIGIBLE")
        matched = set(matching_rules(facts, self.rules))
        eligible = {item.product for item in value.eligibility.products if item.status == "eligible"}
        candidates = set()
        if facts.necessidade_aderente is True and facts.costs_verified:
            if "R001" in matched:
                candidates.add("renegotiation")
            if facts.inadimplente is False and facts.capacidade_pagamento is True:
                if "R004" in matched:
                    candidates.add("credit")
                if "R005" in matched:
                    candidates.add("financing")
                if "R006" in matched:
                    candidates.add("consortium")
            if facts.profile_verified and facts.horizon_verified:
                if ("R007" in matched and facts.liquidity_compatible) or "R008" in matched:
                    candidates.add("investment")
        allowed = [product for product in value.requested_products if product in eligible & candidates
                   and product not in self.limits.blocked_products]
        maximum = 1 if context.financial_level == "tight" else 3
        allowed = allowed[:maximum]
        if not allowed:
            return finish("PRODUCT_BLOCKED")
        result.update(outcome="allow", allowed_actions=["compare_products"],
                      blocked_actions=[action for action in ACTIONS if action != "compare_products"],
                      allowed_products=allowed, blocked_products=[product for product in PRODUCTS if product not in allowed],
                      credit_allowed="credit" in allowed, max_options=maximum,
                      language_constraints=["no_judgment", "no_invented_numbers", "no_pressure"])
        return finish("ALLOWED")
