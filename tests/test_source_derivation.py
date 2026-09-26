import json
from pathlib import Path
import unittest

from scripts.derive_sources import conditions, derive


class SourceDerivationTests(unittest.TestCase):
    def test_regeneration_is_exact_and_complete(self):
        generated = derive()
        for name, content in generated.items():
            self.assertEqual(Path(name).read_text(), content, name)
        rows = [json.loads(row) for row in generated["evals/scenarios.jsonl"].splitlines()]
        self.assertEqual(len(rows), 250)
        self.assertEqual(len({row["id"] for row in rows}), 250)
        self.assertEqual({row["source"]["row"] for row in rows}, set(range(2, 252)))

    def test_predicates_preserve_false_and_conjunction(self):
        self.assertEqual(conditions("inadimplente = NÃO AND risco_saldo_negativo = SIM"), [
            {"field": "inadimplente", "operator": "eq", "value": False},
            {"field": "risco_saldo_negativo", "operator": "eq", "value": True},
        ])
        with self.assertRaises(ValueError):
            conditions("unreviewed > 0")

    def test_voice_absence_does_not_fabricate_guidance(self):
        voice = json.loads(Path("config/voice/source_status.json").read_text())
        self.assertFalse(voice["definitive"])
        for category in ("generation_guidance", "behavior_rules", "safety_rules", "product_restrictions", "human_handoff"):
            self.assertEqual(voice[category], [])
