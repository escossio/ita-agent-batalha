import copy
import json
from pathlib import Path
import unittest
from pydantic import ValidationError
from packages.contracts.models import FinancialSnapshot
from services.finance.engine import MissingData, breakdown, compare_history, costs, project
from services.finance.main import calculate
from test_contracts import CID


def fixture():
    return json.loads(Path("services/data/fixtures/demo-snapshot.json").read_text())


def query(snapshot=None, spend=50000):
    return dict(correlation_id=CID, snapshot=snapshot or fixture(), proposed_spend_cents=spend)


class FinanceTests(unittest.TestCase):
    def test_projection_is_deterministic_and_excludes_salary(self):
        result = project(query())
        self.assertEqual(result, project(query()))
        self.assertEqual(result.base_closing_cents, 110000)
        self.assertEqual(result.closing_cents, 60000)
        self.assertEqual(result.commitments_cents, 75000)
        self.assertEqual(result.estimates_cents, 15000)
        self.assertTrue(result.uncertain)
        self.assertEqual(result.lowest_balance_cents, 60000)

    def test_all_categories_are_accounted_once(self):
        result = breakdown(FinancialSnapshot.model_validate(fixture()))
        self.assertEqual(result.total_cents, 90000)
        self.assertEqual(result.installments_cents, 20000)
        self.assertEqual(result.subscriptions_cents, 5000)
        self.assertEqual(result.recurring_cents, 10000)
        self.assertEqual(result.variable_cents, 15000)

    def test_missing_income_or_incomplete_snapshot_refuses_calculation(self):
        for patch in ({"next_income": None}, {"data_complete": False}):
            with self.subTest(patch=patch), self.assertRaises(MissingData):
                project(query(fixture() | patch))
        status, result = calculate(query(fixture() | {"next_income": None}), CID)
        self.assertEqual((status, result["error"]), (422, "MISSING_DATA"))

    def test_missing_history_does_not_invent_history_or_block_complete_projection(self):
        self.assertIsNone(fixture()["history"])
        self.assertEqual(project(query()).closing_cents, 60000)
        with self.assertRaises(ValidationError):
            compare_history({"previous": None, "current": None})

    def test_insufficient_balance_and_overspend_stay_negative(self):
        self.assertEqual(project(query(fixture() | {"balance_cents": 10000}, 0)).closing_cents, -80000)
        self.assertEqual(project(query(spend=300000)).closing_cents, -190000)
        self.assertEqual(project(query(fixture() | {"balance_cents": -10000}, 0)).closing_cents, -100000)

    def test_cutoff_excludes_same_day_and_includes_overdue_pending_items(self):
        snap = fixture()
        snap["commitments"][0]["due_on"] = "2026-09-19"
        self.assertEqual(project(query(snap)).closing_cents, 100000)
        snap["commitments"][0]["due_on"] = "2026-08-31"
        self.assertEqual(project(query(snap)).closing_cents, 60000)

    def test_estimates_and_estimated_income_mark_uncertainty(self):
        snap = fixture()
        for item in snap["commitments"]:
            item["certainty"] = "confirmed"
        self.assertFalse(project(query(snap)).uncertain)
        snap["next_income"]["certainty"] = "estimated"
        self.assertTrue(project(query(snap)).uncertain)

    def test_money_validation_overflow_and_correlation(self):
        for value in (True, -1, "100", 0.5, 10**13):
            with self.subTest(value=value), self.assertRaises(ValidationError):
                project(query(spend=value))
        with self.assertRaises(ValidationError):
            project(query(fixture() | {"balance_cents": -(10**12)}, 10**12))
        with self.assertRaises(ValueError):
            calculate(query(), CID[:-1] + "2")

    def test_permuting_commitments_does_not_change_result_or_mutate_input(self):
        value = query()
        original = copy.deepcopy(value)
        first = project(value)
        self.assertEqual(value, original)
        value["snapshot"]["commitments"].reverse()
        self.assertEqual(first, project(value))

    def test_history_does_not_double_count_installments(self):
        old = dict(month="2026-07", income_cents=300000, committed_cents=100000,
                   variable_cents=50000, installment_cents=30000, negative_days=3, complete=True)
        new = old | dict(month="2026-08", income_cents=320000, committed_cents=90000,
                         variable_cents=60000, installment_cents=20000, negative_days=1)
        result = compare_history(dict(previous=old, current=new))
        self.assertEqual(result.surplus_delta_cents, 20000)
        self.assertEqual(result.installment_delta_cents, -10000)
        self.assertEqual(result.negative_days_delta, -2)
        with self.assertRaises(MissingData):
            compare_history(dict(previous=old, current=new | {"complete": False}))
        with self.assertRaises(ValueError):
            compare_history(dict(previous=new, current=old))

    def test_costs_require_verified_rate_and_explicit_regime(self):
        value = dict(principal_cents=100000, periodic_rate_basis_points=100, periods=2,
                     regime="simple", rate_verified=True, fees_cents=300)
        self.assertEqual(costs(value).total_cents, 102300)
        self.assertEqual(costs(value | {"regime": "compound"}).total_cents, 102310)
        for patch in ({"rate_verified": False}, {"periodic_rate_basis_points": None}):
            with self.assertRaises(MissingData):
                costs(value | patch)
        self.assertEqual(costs(value | {"periodic_rate_basis_points": 0}).total_cents, 100300)

    def test_cost_rounding_half_up_and_bounds(self):
        value = dict(principal_cents=50, periodic_rate_basis_points=100, periods=1,
                     regime="simple", rate_verified=True, fees_cents=0)
        self.assertEqual(costs(value).interest_cents, 1)
        with self.assertRaises(ValueError):
            costs(value | dict(principal_cents=10**12, periods=600, regime="compound"))
