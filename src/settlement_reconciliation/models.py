from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from enum import StrEnum
from typing import Any


RawRow = dict[str, str]


class MatchStatus(StrEnum):
    MATCHED = "matched"
    MATCHED_WITH_WARNING = "matched_with_warning"
    AMOUNT_MISMATCH = "amount_mismatch"
    DATE_MISMATCH = "date_mismatch"
    CURRENCY_MISMATCH = "currency_mismatch"
    AMBIGUOUS = "ambiguous"
    MISSING_BANK_DEPOSIT = "missing_bank_deposit"
    UNEXPLAINED_BANK_DEPOSIT = "unexplained_bank_deposit"


@dataclass(frozen=True)
class RawRecord:
    source_file: str
    row_number: int
    raw: RawRow


@dataclass(frozen=True)
class SettlementRecord(RawRecord):
    settlement_id: str
    platform: str = ""
    store: str = ""
    currency: str = ""
    settlement_start_date: date | None = None
    settlement_end_date: date | None = None
    expected_payout_date: date | None = None
    gross_amount: Decimal | None = None
    fees_amount: Decimal | None = None
    refund_amount: Decimal | None = None
    adjustment_amount: Decimal | None = None
    net_amount: Decimal = Decimal("0")
    reference: str = ""


@dataclass(frozen=True)
class BankTransaction(RawRecord):
    transaction_id: str
    account: str = ""
    transaction_date: date | None = None
    value_date: date | None = None
    currency: str = ""
    amount: Decimal = Decimal("0")
    direction: str = ""
    counterparty: str = ""
    reference: str = ""
    description: str = ""


@dataclass(frozen=True)
class NormalizationIssue:
    source_file: str
    row_number: int
    kind: str
    message: str
    raw: RawRow = field(default_factory=dict)


@dataclass(frozen=True)
class MatchCandidate:
    settlement: SettlementRecord
    bank_transaction: BankTransaction
    confidence: int
    difference_amount: Decimal
    date_delta_days: int | None
    reasons: tuple[str, ...]
    amount_within_tolerance: bool
    currency_matches: bool
    date_within_window: bool
    reference_matches: bool


@dataclass(frozen=True)
class MatchResult:
    settlement: SettlementRecord | None
    bank_transaction: BankTransaction | None
    status: MatchStatus
    confidence: int
    difference_amount: Decimal | None = None
    date_delta_days: int | None = None
    reasons: tuple[str, ...] = ()
    candidates: tuple[MatchCandidate, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)

