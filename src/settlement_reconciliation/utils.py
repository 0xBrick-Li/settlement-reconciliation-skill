from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal, InvalidOperation
import re


EMPTY_VALUES = {"", "-", "—", "n/a", "na", "null", "none"}


def clean_text(value: object) -> str:
    if value is None:
        return ""
    return str(value).strip()


def is_empty(value: object) -> bool:
    return clean_text(value).lower() in EMPTY_VALUES


def normalize_currency(value: object) -> str:
    return clean_text(value).upper()


def parse_decimal(value: object) -> Decimal:
    text = clean_text(value)
    if is_empty(text):
        raise ValueError("missing decimal value")

    negative = False
    if text.startswith("(") and text.endswith(")"):
        negative = True
        text = text[1:-1]

    text = re.sub(r"[^0-9.\-]", "", text)
    if text in {"", "-", ".", "-."}:
        raise ValueError("invalid decimal value")

    try:
        amount = Decimal(text)
    except InvalidOperation as exc:
        raise ValueError(f"invalid decimal value: {value}") from exc

    return -amount if negative else amount


def parse_optional_decimal(value: object) -> Decimal | None:
    if is_empty(value):
        return None
    return parse_decimal(value)


def parse_date(value: object) -> date:
    text = clean_text(value)
    if is_empty(text):
        raise ValueError("missing date value")

    formats = (
        "%Y-%m-%d",
        "%Y/%m/%d",
        "%m/%d/%Y",
        "%d/%m/%Y",
        "%Y-%m-%d %H:%M:%S",
        "%Y/%m/%d %H:%M:%S",
    )
    for fmt in formats:
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            pass

    try:
        return datetime.fromisoformat(text).date()
    except ValueError as exc:
        raise ValueError(f"invalid date value: {value}") from exc


def parse_optional_date(value: object) -> date | None:
    if is_empty(value):
        return None
    return parse_date(value)


def normalize_reference(value: object) -> str:
    return re.sub(r"\s+", " ", clean_text(value)).lower()


def references_overlap(left: str, right: str) -> bool:
    left_norm = normalize_reference(left)
    right_norm = normalize_reference(right)
    if not left_norm or not right_norm:
        return False
    return left_norm in right_norm or right_norm in left_norm

