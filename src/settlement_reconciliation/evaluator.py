from __future__ import annotations

from collections import Counter
from decimal import Decimal

from settlement_reconciliation.config import ReconciliationConfig
from settlement_reconciliation.models import (
    BankTransaction,
    MatchCandidate,
    MatchResult,
    MatchStatus,
    SettlementRecord,
)


def evaluate_matches(
    settlements: list[SettlementRecord],
    bank_transactions: list[BankTransaction],
    candidates_by_settlement: dict[str, list[MatchCandidate]],
    config: ReconciliationConfig,
) -> list[MatchResult]:
    best_candidates: dict[str, MatchCandidate] = {}
    ambiguous_settlements: set[str] = set()

    for settlement in settlements:
        candidates = _meaningful_candidates(candidates_by_settlement.get(settlement.settlement_id, []))
        if not candidates:
            continue
        top = candidates[0]
        if _is_ambiguous(candidates):
            ambiguous_settlements.add(settlement.settlement_id)
        best_candidates[settlement.settlement_id] = top

    bank_usage = Counter(candidate.bank_transaction.transaction_id for candidate in best_candidates.values())
    matched_bank_ids: set[str] = set()
    linked_bank_ids: set[str] = set()
    results: list[MatchResult] = []

    for settlement in settlements:
        candidates = _meaningful_candidates(candidates_by_settlement.get(settlement.settlement_id, []))
        top = best_candidates.get(settlement.settlement_id)
        if top is None:
            results.append(
                MatchResult(
                    settlement=settlement,
                    bank_transaction=None,
                    status=MatchStatus.MISSING_BANK_DEPOSIT,
                    confidence=0,
                    difference_amount=None,
                    reasons=("no bank candidate found",),
                )
            )
            continue

        if (
            settlement.settlement_id in ambiguous_settlements
            or (bank_usage[top.bank_transaction.transaction_id] > 1 and not config.allow_many_to_one)
        ):
            linked_bank_ids.update(candidate.bank_transaction.transaction_id for candidate in candidates)
            results.append(_result_from_candidate(top, MatchStatus.AMBIGUOUS, candidates, "multiple plausible candidates"))
            continue

        status = _classify_candidate(top)
        linked_bank_ids.add(top.bank_transaction.transaction_id)
        if status in {MatchStatus.MATCHED, MatchStatus.MATCHED_WITH_WARNING}:
            matched_bank_ids.add(top.bank_transaction.transaction_id)
        results.append(_result_from_candidate(top, status, candidates))

    for transaction in bank_transactions:
        if transaction.transaction_id not in linked_bank_ids:
            results.append(
                MatchResult(
                    settlement=None,
                    bank_transaction=transaction,
                    status=MatchStatus.UNEXPLAINED_BANK_DEPOSIT,
                    confidence=0,
                    difference_amount=transaction.amount,
                    reasons=("bank transaction was not matched to a settlement",),
                )
            )

    return results


def _meaningful_candidates(candidates: list[MatchCandidate]) -> list[MatchCandidate]:
    return [candidate for candidate in candidates if candidate.confidence >= 50 or candidate.reference_matches]


def _is_ambiguous(candidates: list[MatchCandidate]) -> bool:
    if len(candidates) < 2:
        return False
    top, second = candidates[0], candidates[1]
    if top.confidence < 70:
        return False
    return top.confidence - second.confidence <= 10


def _classify_candidate(candidate: MatchCandidate) -> MatchStatus:
    if not candidate.currency_matches:
        return MatchStatus.CURRENCY_MISMATCH
    if not candidate.amount_within_tolerance:
        return MatchStatus.AMOUNT_MISMATCH
    if not candidate.date_within_window:
        return MatchStatus.DATE_MISMATCH
    if candidate.confidence >= 85:
        return MatchStatus.MATCHED
    if candidate.confidence >= 70:
        return MatchStatus.MATCHED_WITH_WARNING
    return MatchStatus.MISSING_BANK_DEPOSIT


def _result_from_candidate(
    candidate: MatchCandidate,
    status: MatchStatus,
    candidates: list[MatchCandidate],
    extra_reason: str | None = None,
) -> MatchResult:
    reasons = list(candidate.reasons)
    if extra_reason:
        reasons.append(extra_reason)
    return MatchResult(
        settlement=candidate.settlement,
        bank_transaction=candidate.bank_transaction,
        status=status,
        confidence=candidate.confidence,
        difference_amount=candidate.difference_amount.quantize(Decimal("0.01")),
        date_delta_days=candidate.date_delta_days,
        reasons=tuple(reasons),
        candidates=tuple(candidates),
    )
