from __future__ import annotations

import argparse
from pathlib import Path

from settlement_reconciliation.config import ReconciliationConfig
from settlement_reconciliation.evaluator import evaluate_matches
from settlement_reconciliation.loader import load_tabular_file
from settlement_reconciliation.matcher import build_match_candidates
from settlement_reconciliation.normalizer import normalize_bank, normalize_settlements
from settlement_reconciliation.reporter import write_reports


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Settlement-level reconciliation for payouts and bank statements.")
    parser.add_argument("--settlement", required=True, help="Path to settlement CSV/XLSX file.")
    parser.add_argument("--bank", required=True, help="Path to bank statement CSV/XLSX file.")
    parser.add_argument("--config", help="Optional YAML/JSON field mapping config.")
    parser.add_argument("--out", required=True, help="Output directory for reconciliation reports.")
    parser.add_argument("--amount-tolerance", help="Override amount tolerance, e.g. 0.01.")
    parser.add_argument("--date-window-days", type=int, help="Override date window in days.")
    args = parser.parse_args(argv)

    config = ReconciliationConfig.load(args.config).with_overrides(
        amount_tolerance=args.amount_tolerance,
        date_window_days=args.date_window_days,
    )

    settlement_rows = load_tabular_file(args.settlement)
    bank_rows = load_tabular_file(args.bank)
    settlements, settlement_issues = normalize_settlements(settlement_rows, args.settlement, config)
    bank_transactions, bank_issues = normalize_bank(bank_rows, args.bank, config)

    candidates = build_match_candidates(settlements, bank_transactions, config)
    results = evaluate_matches(settlements, bank_transactions, candidates, config)
    write_reports(results, Path(args.out), settlement_issues + bank_issues)

    print(f"Wrote reconciliation reports to {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

