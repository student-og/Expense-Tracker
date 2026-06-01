import tempfile
import unittest
from pathlib import Path

from expense_tracker import ExpenseTracker


class ExpenseTrackerTests(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        base = Path(self.tmp_dir.name)
        self.tracker = ExpenseTracker(
            expenses_file=str(base / "expenses.csv"),
            budgets_file=str(base / "budgets.csv"),
        )

    def tearDown(self):
        self.tmp_dir.cleanup()

    def test_add_expense_and_filter_history(self):
        self.tracker.add_expense(amount=12.5, category="Food", description="Lunch", expense_date="2026-06-01")
        self.tracker.add_expense(amount=20, category="Transport", description="Taxi", expense_date="2026-06-02")

        june_expenses = self.tracker.get_expenses(year=2026, month=6)
        self.assertEqual(len(june_expenses), 2)

        food_expenses = self.tracker.get_expenses(year=2026, month=6, category="food")
        self.assertEqual(len(food_expenses), 1)
        self.assertEqual(food_expenses[0].description, "Lunch")

    def test_monthly_summary_and_budget_monitoring(self):
        self.tracker.add_expense(amount=120, category="Rent", expense_date="2026-06-01")
        self.tracker.add_expense(amount=30, category="Food", expense_date="2026-06-03")
        self.tracker.set_budget(year=2026, month=6, amount=200)

        summary = self.tracker.monthly_summary(year=2026, month=6)

        self.assertEqual(summary["total"], 150.0)
        self.assertEqual(summary["by_category"]["Food"], 30.0)
        self.assertEqual(summary["by_category"]["Rent"], 120.0)
        self.assertEqual(summary["remaining"], 50.0)
        self.assertFalse(summary["over_budget"])

    def test_input_validation(self):
        with self.assertRaises(ValueError):
            self.tracker.add_expense(amount=-1, category="Food", expense_date="2026-06-01")

        with self.assertRaises(ValueError):
            self.tracker.add_expense(amount=10, category="", expense_date="2026-06-01")

        with self.assertRaises(ValueError):
            self.tracker.add_expense(amount=10, category="Food", expense_date="01-06-2026")


if __name__ == "__main__":
    unittest.main()
