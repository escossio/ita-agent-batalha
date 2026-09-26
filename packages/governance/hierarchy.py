"""Arbitragem de precedência; não concede capacidades nem interpreta linguagem."""
from enum import IntEnum
from typing import Literal

from packages.contracts.models import Record


class Level(IntEnum):
    PERSON_SAFETY = 1
    MANDATORY_RESTRICTIONS = 2
    AUTHORIZATION = 3
    FINANCIAL_RULES = 4
    ELIGIBILITY = 5
    CONVERSATION = 6
    VOICE = 7


class Finding(Record):
    level: Level
    effect: Literal["allow", "deny", "handoff"]


def resolve(findings: list[Finding]) -> str:
    """Any restriction survives a lower/higher priority suggestion to allow."""
    restrictions = [item for item in findings if item.effect != "allow"]
    if restrictions:
        # Same-level deny wins; priority decides the primary response, never grants.
        return min(restrictions, key=lambda item: (item.level, item.effect != "deny")).effect
    return "allow" if findings else "deny"
