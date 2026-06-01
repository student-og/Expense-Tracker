# Expense-Tracker

Expense Tracker is a lightweight personal finance management app for students.
It records daily expenses in CSV files, categorizes spending, shows monthly summaries,
and monitors monthly budget usage.

## Features

- Add expenses with date, amount, category, and optional description
- Categorize spending and filter expense history by month/year/category
- Generate monthly expense summaries with category totals
- Track expense history stored in CSV files
- Monitor monthly budgets with over/within-budget status
- Validate user input for date format, category, and amount

## Requirements

- Python 3.9+

## Usage

All commands use CSV files (`expenses.csv` and `budgets.csv`) by default.
You can override with `--expenses-file` and `--budgets-file`.

### Add an expense

```bash
python expense_tracker.py add --amount 12.50 --category Food --description "Lunch" --date 2026-06-01
```

### View expense history

```bash
python expense_tracker.py history --year 2026 --month 6
python expense_tracker.py history --year 2026 --month 6 --category Food
```

### Set a monthly budget

```bash
python expense_tracker.py set-budget --year 2026 --month 6 --amount 500
```

### View monthly summary

```bash
python expense_tracker.py summary --year 2026 --month 6
```
