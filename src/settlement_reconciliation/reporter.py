from __future__ import annotations

import csv
from collections import Counter
from decimal import Decimal
from pathlib import Path

from settlement_reconciliation.models import MatchResult, MatchStatus, NormalizationIssue


MATCHED_STATUSES = {MatchStatus.MATCHED, MatchStatus.MATCHED_WITH_WARNING}


def write_reports(
    results: list[MatchResult],
    out_dir: str | Path,
    normalization_issues: list[NormalizationIssue] | None = None,
) -> None:
    destination = Path(out_dir)
    destination.mkdir(parents=True, exist_ok=True)
    issues = normalization_issues or []

    _write_summary(destination / "reconciliation_summary.csv", results, issues)
    _write_rows(destination / "matched.csv", [result for result in results if result.status in MATCHED_STATUSES])
    _write_rows(destination / "exceptions.csv", [result for result in results if result.status not in MATCHED_STATUSES])
    _write_rows(
        destination / "unmatched_settlements.csv",
        [result for result in results if result.status == MatchStatus.MISSING_BANK_DEPOSIT],
    )
    _write_rows(
        destination / "unmatched_bank_transactions.csv",
        [result for result in results if result.status == MatchStatus.UNEXPLAINED_BANK_DEPOSIT],
    )
    _write_markdown(destination / "reconciliation_report.md", results, issues)


def _write_summary(path: Path, results: list[MatchResult], issues: list[NormalizationIssue]) -> None:
    counts = Counter(result.status for result in results)
    settlement_results = [result for result in results if result.settlement is not None]
    bank_results = [result for result in results if result.bank_transaction is not None]
    matched = [result for result in results if result.status in MATCHED_STATUSES and result.bank_transaction is not None]
    total_settlement_amount = sum((result.settlement.net_amount for result in settlement_results if result.settlement), Decimal("0"))
    total_matched_bank_amount = sum((result.bank_transaction.amount for result in matched if result.bank_transaction), Decimal("0"))
    total_difference = sum((result.difference_amount or Decimal("0") for result in matched), Decimal("0"))

    rows = [
        ("total_settlements", str(len(settlement_results))),
        ("total_bank_transactions", str(len({result.bank_transaction.transaction_id for result in bank_results if result.bank_transaction}))),
        ("matched_count", str(counts[MatchStatus.MATCHED])),
        ("warning_count", str(counts[MatchStatus.MATCHED_WITH_WARNING])),
        ("exception_count", str(sum(count for status, count in counts.items() if status not in MATCHED_STATUSES) + len(issues))),
        ("unmatched_settlement_count", str(counts[MatchStatus.MISSING_BANK_DEPOSIT])),
        ("unmatched_bank_count", str(counts[MatchStatus.UNEXPLAINED_BANK_DEPOSIT])),
        ("normalization_issue_count", str(len(issues))),
        ("total_settlement_amount", _money(total_settlement_amount)),
        ("total_matched_bank_amount", _money(total_matched_bank_amount)),
        ("total_difference", _money(total_difference)),
    ]

    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["metric", "value"])
        writer.writerows(rows)


def _write_rows(path: Path, results: list[MatchResult]) -> None:
    fieldnames = [
        "status",
        "settlement_id",
        "bank_transaction_id",
        "platform",
        "store",
        "currency",
        "settlement_net_amount",
        "bank_amount",
        "difference_amount",
        "expected_payout_date",
        "bank_transaction_date",
        "date_delta_days",
        "confidence",
        "reasons",
        "settlement_source_row",
        "bank_source_row",
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for result in results:
            writer.writerow(_row(result))


def _write_markdown(path: Path, results: list[MatchResult], issues: list[NormalizationIssue]) -> None:
    counts = Counter(result.status for result in results)
    settlement_count = len([result for result in results if result.settlement is not None])
    matched_count = counts[MatchStatus.MATCHED] + counts[MatchStatus.MATCHED_WITH_WARNING]
    match_rate = (matched_count / settlement_count * 100) if settlement_count else 0
    total_difference = sum(
        (result.difference_amount or Decimal("0") for result in results if result.status in MATCHED_STATUSES),
        Decimal("0"),
    )

    lines = [
        "# Reconciliation Report",
        "",
        f"- Match rate: {match_rate:.2f}%",
        f"- Matched settlements: {matched_count}",
        f"- Exceptions: {sum(count for status, count in counts.items() if status not in MATCHED_STATUSES) + len(issues)}",
        f"- Total matched difference: {_money(total_difference)}",
        "",
        "## Status Counts",
        "",
    ]
    for status, count in sorted(counts.items(), key=lambda item: item[0].value):
        lines.append(f"- {status.value}: {count}")
    if issues:
        lines.extend(["", "## Normalization Issues", ""])
        for issue in issues[:20]:
            lines.append(f"- {issue.kind} row {issue.row_number}: {issue.message}")

    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _row(result: MatchResult) -> dict[str, str]:
    settlement = result.settlement
    bank = result.bank_transaction
    currency = settlement.currency if settlement else bank.currency if bank else ""
    return {
        "status": result.status.value,
        "settlement_id": settlement.settlement_id if settlement else "",
        "bank_transaction_id": bank.transaction_id if bank else "",
        "platform": settlement.platform if settlement else "",
        "store": settlement.store if settlement else "",
        "currency": currency,
        "settlement_net_amount": _money(settlement.net_amount) if settlement else "",
        "bank_amount": _money(bank.amount) if bank else "",
        "difference_amount": _money(result.difference_amount) if result.difference_amount is not None else "",
        "expected_payout_date": str(settlement.expected_payout_date or "") if settlement else "",
        "bank_transaction_date": str(bank.transaction_date or "") if bank else "",
        "date_delta_days": "" if result.date_delta_days is None else str(result.date_delta_days),
        "confidence": str(result.confidence),
        "reasons": "; ".join(result.reasons),
        "settlement_source_row": str(settlement.row_number) if settlement else "",
        "bank_source_row": str(bank.row_number) if bank else "",
    }


def _money(value: Decimal | None) -> str:
    if value is None:
        return ""
    return str(value.quantize(Decimal("0.01")))

