from __future__ import annotations

import argparse
import csv
from collections import defaultdict
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Dict, List, Optional


DATE_FORMAT = "%Y-%m-%d"


@dataclass
class Expense:
    expense_date: str
    amount: float
    category: str
    description: str


class ExpenseTracker:
    def __init__(self, expenses_file: str = "expenses.csv", budgets_file: str = "budgets.csv") -> None:
        self.expenses_file = Path(expenses_file)
        self.budgets_file = Path(budgets_file)
        self._ensure_expenses_file()
        self._ensure_budgets_file()

    def _ensure_expenses_file(self) -> None:
        if not self.expenses_file.exists():
            with self.expenses_file.open("w", newline="", encoding="utf-8") as handle:
                writer = csv.DictWriter(handle, fieldnames=["date", "amount", "category", "description"])
                writer.writeheader()

    def _ensure_budgets_file(self) -> None:
        if not self.budgets_file.exists():
            with self.budgets_file.open("w", newline="", encoding="utf-8") as handle:
                writer = csv.DictWriter(handle, fieldnames=["year", "month", "budget"])
                writer.writeheader()

    @staticmethod
    def _parse_date(raw_date: str) -> datetime:
        try:
            return datetime.strptime(raw_date, DATE_FORMAT)
        except ValueError as exc:
            raise ValueError(f"Date must be in {DATE_FORMAT} format") from exc

    @staticmethod
    def _validate_amount(amount: float) -> float:
        try:
            normalized = float(amount)
        except (TypeError, ValueError) as exc:
            raise ValueError("Amount must be a number") from exc

        if normalized <= 0:
            raise ValueError("Amount must be greater than 0")
        return round(normalized, 2)

    @staticmethod
    def _validate_category(category: str) -> str:
        if not category or not category.strip():
            raise ValueError("Category is required")
        return category.strip()

    def add_expense(self, amount: float, category: str, description: str = "", expense_date: Optional[str] = None) -> Expense:
        expense_date = expense_date or date.today().strftime(DATE_FORMAT)
        parsed_date = self._parse_date(expense_date)
        normalized_amount = self._validate_amount(amount)
        normalized_category = self._validate_category(category)
        normalized_description = (description or "").strip()

        expense = Expense(
            expense_date=parsed_date.strftime(DATE_FORMAT),
            amount=normalized_amount,
            category=normalized_category,
            description=normalized_description,
        )

        with self.expenses_file.open("a", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=["date", "amount", "category", "description"])
            writer.writerow(
                {
                    "date": expense.expense_date,
                    "amount": f"{expense.amount:.2f}",
                    "category": expense.category,
                    "description": expense.description,
                }
            )

        return expense

    def get_expenses(self, year: Optional[int] = None, month: Optional[int] = None, category: Optional[str] = None) -> List[Expense]:
        records: List[Expense] = []
        with self.expenses_file.open("r", newline="", encoding="utf-8") as handle:
            reader = csv.DictReader(handle)
            for row in reader:
                row_date = datetime.strptime(row["date"], DATE_FORMAT)

                if year and row_date.year != year:
                    continue
                if month and row_date.month != month:
                    continue
                if category and row["category"].strip().lower() != category.strip().lower():
                    continue

                records.append(
                    Expense(
                        expense_date=row["date"],
                        amount=float(row["amount"]),
                        category=row["category"],
                        description=row.get("description", ""),
                    )
                )

        return sorted(records, key=lambda item: item.expense_date)

    def monthly_summary(self, year: int, month: int) -> Dict[str, object]:
        expenses = self.get_expenses(year=year, month=month)
        by_category: Dict[str, float] = defaultdict(float)
        total = 0.0

        for entry in expenses:
            total += entry.amount
            by_category[entry.category] += entry.amount

        budget = self.get_budget(year=year, month=month)
        remaining = None if budget is None else round(budget - total, 2)

        return {
            "year": year,
            "month": month,
            "total": round(total, 2),
            "count": len(expenses),
            "by_category": {key: round(value, 2) for key, value in sorted(by_category.items())},
            "budget": budget,
            "remaining": remaining,
            "over_budget": False if budget is None else total > budget,
        }

    def set_budget(self, year: int, month: int, amount: float) -> float:
        normalized_amount = self._validate_amount(amount)
        rows = []

        with self.budgets_file.open("r", newline="", encoding="utf-8") as handle:
            reader = csv.DictReader(handle)
            for row in reader:
                if int(row["year"]) == year and int(row["month"]) == month:
                    row["budget"] = f"{normalized_amount:.2f}"
                rows.append(row)

        if not any(int(row["year"]) == year and int(row["month"]) == month for row in rows):
            rows.append({"year": str(year), "month": str(month), "budget": f"{normalized_amount:.2f}"})

        with self.budgets_file.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=["year", "month", "budget"])
            writer.writeheader()
            writer.writerows(rows)

        return normalized_amount

    def get_budget(self, year: int, month: int) -> Optional[float]:
        with self.budgets_file.open("r", newline="", encoding="utf-8") as handle:
            reader = csv.DictReader(handle)
            for row in reader:
                if int(row["year"]) == year and int(row["month"]) == month:
                    return float(row["budget"])
        return None


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Track and summarize personal expenses")
    parser.add_argument("--expenses-file", default="expenses.csv", help="CSV file for expenses")
    parser.add_argument("--budgets-file", default="budgets.csv", help="CSV file for monthly budgets")

    subparsers = parser.add_subparsers(dest="command", required=True)

    add_parser = subparsers.add_parser("add", help="Add an expense")
    add_parser.add_argument("--amount", type=float, required=True)
    add_parser.add_argument("--category", required=True)
    add_parser.add_argument("--description", default="")
    add_parser.add_argument("--date", dest="expense_date", default=None, help="Date in YYYY-MM-DD")

    history_parser = subparsers.add_parser("history", help="Show expense history")
    history_parser.add_argument("--year", type=int)
    history_parser.add_argument("--month", type=int)
    history_parser.add_argument("--category")

    summary_parser = subparsers.add_parser("summary", help="Show monthly summary")
    summary_parser.add_argument("--year", type=int, required=True)
    summary_parser.add_argument("--month", type=int, required=True)

    budget_parser = subparsers.add_parser("set-budget", help="Set monthly budget")
    budget_parser.add_argument("--year", type=int, required=True)
    budget_parser.add_argument("--month", type=int, required=True)
    budget_parser.add_argument("--amount", type=float, required=True)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    tracker = ExpenseTracker(expenses_file=args.expenses_file, budgets_file=args.budgets_file)

    try:
        if args.command == "add":
            entry = tracker.add_expense(
                amount=args.amount,
                category=args.category,
                description=args.description,
                expense_date=args.expense_date,
            )
            print(
                f"Added expense: {entry.expense_date} | {entry.category} | "
                f"${entry.amount:.2f} | {entry.description}"
            )
        elif args.command == "history":
            history = tracker.get_expenses(year=args.year, month=args.month, category=args.category)
            if not history:
                print("No expenses found.")
                return

            for item in history:
                print(f"{item.expense_date} | {item.category} | ${item.amount:.2f} | {item.description}")
        elif args.command == "summary":
            report = tracker.monthly_summary(year=args.year, month=args.month)
            print(f"Summary for {report['year']}-{report['month']:02d}")
            print(f"Total Expenses: ${report['total']:.2f}")
            print(f"Transactions: {report['count']}")
            print("By Category:")
            if report["by_category"]:
                for category, value in report["by_category"].items():
                    print(f" - {category}: ${value:.2f}")
            else:
                print(" - None")

            if report["budget"] is not None:
                print(f"Budget: ${report['budget']:.2f}")
                print(f"Remaining: ${report['remaining']:.2f}")
                if report["over_budget"]:
                    print("Status: OVER BUDGET")
                else:
                    print("Status: WITHIN BUDGET")
        elif args.command == "set-budget":
            value = tracker.set_budget(year=args.year, month=args.month, amount=args.amount)
            print(f"Budget set for {args.year}-{args.month:02d}: ${value:.2f}")
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc


if __name__ == "__main__":
    main()
