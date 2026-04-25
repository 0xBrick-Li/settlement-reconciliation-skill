from __future__ import annotations

from decimal import Decimal

from settlement_reconciliation.config import ReconciliationConfig
from settlement_reconciliation.models import BankTransaction, MatchCandidate, SettlementRecord
from settlement_reconciliation.utils import references_overlap


def build_match_candidates(
    settlements: list[SettlementRecord],
    bank_transactions: list[BankTransaction],
    config: ReconciliationConfig,
) -> dict[str, list[MatchCandidate]]:
    candidates: dict[str, list[MatchCandidate]] = {}
    for settlement in settlements:
        settlement_candidates: list[MatchCandidate] = []
        for transaction in bank_transactions:
            candidate = score_candidate(settlement, transaction, config)
            if candidate.confidence > 0:
                settlement_candidates.append(candidate)
        candidates[settlement.settlement_id] = sorted(
            settlement_candidates,
            key=lambda item: (item.confidence, -abs(item.difference_amount)),
            reverse=True,
        )
    return candidates


def score_candidate(
    settlement: SettlementRecord,
    transaction: BankTransaction,
    config: ReconciliationConfig,
) -> MatchCandidate:
    confidence = 0
    reasons: list[str] = []
    difference = transaction.amount - settlement.net_amount

    amount_within_tolerance = abs(difference) <= config.amount_tolerance
    currency_matches = bool(settlement.currency and transaction.currency and settlement.currency == transaction.currency)
    date_delta_days = _date_delta_days(settlement, transaction)
    date_within_window = date_delta_days is not None and abs(date_delta_days) <= config.date_window_days
    reference_matches = references_overlap(settlement.reference, transaction.reference) or references_overlap(
        settlement.reference,
        transaction.description,
    )

    if amount_within_tolerance:
        confidence += 50
        reasons.append("amount within tolerance")
    elif settlement.reference and (reference_matches or date_within_window):
        reasons.append("amount differs beyond tolerance")

    if currency_matches:
        confidence += 20
        reasons.append("currency matches")
    elif settlement.currency or transaction.currency:
        reasons.append("currency differs")

    if date_within_window:
        confidence += 15
        reasons.append("date within payout window")
    elif date_delta_days is not None and amount_within_tolerance:
        reasons.append("date outside payout window")

    if reference_matches:
        confidence += 15
        reasons.append("reference matches")

    if config.currency_required and not currency_matches:
        confidence = min(confidence, 65)

    return MatchCandidate(
        settlement=settlement,
        bank_transaction=transaction,
        confidence=confidence,
        difference_amount=difference,
        date_delta_days=date_delta_days,
        reasons=tuple(reasons),
        amount_within_tolerance=amount_within_tolerance,
        currency_matches=currency_matches,
        date_within_window=date_within_window,
        reference_matches=reference_matches,
    )


def _date_delta_days(settlement: SettlementRecord, transaction: BankTransaction) -> int | None:
    settlement_date = settlement.expected_payout_date or settlement.settlement_end_date
    transaction_date = transaction.transaction_date or transaction.value_date
    if settlement_date is None or transaction_date is None:
        return None
    return (transaction_date - settlement_date).days

