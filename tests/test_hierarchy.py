import json
from pathlib import Path
import unittest
from packages.governance.hierarchy import Finding, Level, resolve


class HierarchyTests(unittest.TestCase):
    def test_documented_order_matches_arbitration(self):
        config = json.loads(Path("config/policy_hierarchy.json").read_text())
        self.assertEqual(config["precedence"], [level.name.lower() for level in Level])
        self.assertEqual(resolve([]), "deny")

    def test_no_level_can_override_a_deny_with_an_allow(self):
        for denying in Level:
            for allowing in Level:
                self.assertEqual(resolve([Finding(level=denying, effect="deny"),
                                          Finding(level=allowing, effect="allow")]), "deny")

    def test_person_safety_handoff_cannot_grant_authority(self):
        self.assertEqual(resolve([Finding(level=Level.PERSON_SAFETY, effect="handoff"),
                                  Finding(level=Level.VOICE, effect="allow")]), "handoff")

    def test_same_level_deny_wins_independent_of_input_order(self):
        items = [Finding(level=Level.CONVERSATION, effect="handoff"),
                 Finding(level=Level.CONVERSATION, effect="deny")]
        self.assertEqual(resolve(items), "deny")
        self.assertEqual(resolve(items[::-1]), "deny")
