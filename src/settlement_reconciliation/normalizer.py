from __future__ import annotations

from pathlib import Path

from settlement_reconciliation.config import ReconciliationConfig
from settlement_reconciliation.models import (
    BankTransaction,
    NormalizationIssue,
    RawRow,
    SettlementRecord,
)
from settlement_reconciliation.utils import (
    clean_text,
    normalize_currency,
    parse_decimal,
    parse_optional_date,
    parse_optional_decimal,
)


def normalize_settlements(
    rows: list[RawRow],
    source_file: str | Path,
    config: ReconciliationConfig,
) -> tuple[list[SettlementRecord], list[NormalizationIssue]]:
    records: list[SettlementRecord] = []
    issues: list[NormalizationIssue] = []
    source = str(source_file)

    for index, row in enumerate(rows, start=2):
        try:
            net_amount = parse_decimal(_get(row, config.settlement_fields, "net_amount"))
            record = SettlementRecord(
                source_file=source,
                row_number=index,
                raw=row,
                settlement_id=_get(row, config.settlement_fields, "settlement_id") or f"settlement-row-{index}",
                platform=_get(row, config.settlement_fields, "platform"),
                store=_get(row, config.settlement_fields, "store"),
                currency=normalize_currency(_get(row, config.settlement_fields, "currency")),
                settlement_start_date=parse_optional_date(_get(row, config.settlement_fields, "settlement_start_date")),
                settlement_end_date=parse_optional_date(_get(row, config.settlement_fields, "settlement_end_date")),
                expected_payout_date=parse_optional_date(_get(row, config.settlement_fields, "expected_payout_date")),
                gross_amount=parse_optional_decimal(_get(row, config.settlement_fields, "gross_amount")),
                fees_amount=parse_optional_decimal(_get(row, config.settlement_fields, "fees_amount")),
                refund_amount=parse_optional_decimal(_get(row, config.settlement_fields, "refund_amount")),
                adjustment_amount=parse_optional_decimal(_get(row, config.settlement_fields, "adjustment_amount")),
                net_amount=net_amount,
                reference=_get(row, config.settlement_fields, "reference"),
            )
            records.append(record)
        except ValueError as exc:
            issues.append(NormalizationIssue(source, index, "settlement", str(exc), row))

    return records, issues


def normalize_bank(
    rows: list[RawRow],
    source_file: str | Path,
    config: ReconciliationConfig,
) -> tuple[list[BankTransaction], list[NormalizationIssue]]:
    records: list[BankTransaction] = []
    issues: list[NormalizationIssue] = []
    source = str(source_file)

    for index, row in enumerate(rows, start=2):
        try:
            amount = parse_decimal(_get(row, config.bank_fields, "amount"))
            direction = _get(row, config.bank_fields, "direction")
            if direction.lower() in {"debit", "withdrawal", "out", "payment"}:
                amount = -abs(amount)
            elif direction.lower() in {"credit", "deposit", "in", "receipt"}:
                amount = abs(amount)

            record = BankTransaction(
                source_file=source,
                row_number=index,
                raw=row,
                transaction_id=_get(row, config.bank_fields, "transaction_id") or f"bank-row-{index}",
                account=_get(row, config.bank_fields, "account"),
                transaction_date=parse_optional_date(_get(row, config.bank_fields, "transaction_date")),
                value_date=parse_optional_date(_get(row, config.bank_fields, "value_date")),
                currency=normalize_currency(_get(row, config.bank_fields, "currency")),
                amount=amount,
                direction=direction,
                counterparty=_get(row, config.bank_fields, "counterparty"),
                reference=_get(row, config.bank_fields, "reference"),
                description=_get(row, config.bank_fields, "description"),
            )
            records.append(record)
        except ValueError as exc:
            issues.append(NormalizationIssue(source, index, "bank", str(exc), row))

    return records, issues


def _get(row: RawRow, fields: dict[str, list[str]], key: str) -> str:
    aliases = fields.get(key, [])
    exact = {name: value for name, value in row.items()}
    lowered = {name.lower().strip(): value for name, value in row.items()}
    for alias in aliases:
        if alias in exact:
            return clean_text(exact[alias])
        value = lowered.get(alias.lower().strip())
        if value is not None:
            return clean_text(value)
    return ""

