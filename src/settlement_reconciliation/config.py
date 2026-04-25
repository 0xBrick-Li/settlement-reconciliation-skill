from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from pathlib import Path
from typing import Any

from settlement_reconciliation.errors import ConfigError


DEFAULT_SETTLEMENT_FIELDS: dict[str, list[str]] = {
    "settlement_id": ["settlement_id", "Settlement ID", "Payout ID", "Batch ID"],
    "platform": ["platform", "Platform"],
    "store": ["store", "Store", "Shop"],
    "currency": ["currency", "Currency"],
    "settlement_start_date": ["settlement_start_date", "Settlement Start Date", "Start Date"],
    "settlement_end_date": ["settlement_end_date", "Settlement End Date", "End Date"],
    "expected_payout_date": ["expected_payout_date", "Expected Payout Date", "Payout Date"],
    "gross_amount": ["gross_amount", "Gross Amount"],
    "fees_amount": ["fees_amount", "Fees", "Fee Amount"],
    "refund_amount": ["refund_amount", "Refunds", "Refund Amount"],
    "adjustment_amount": ["adjustment_amount", "Adjustments", "Adjustment Amount"],
    "net_amount": ["net_amount", "Net Amount", "Payout Amount", "Amount Paid"],
    "reference": ["reference", "Reference", "Payout Reference"],
}


DEFAULT_BANK_FIELDS: dict[str, list[str]] = {
    "transaction_id": ["transaction_id", "Transaction ID", "Bank Transaction ID"],
    "account": ["account", "Account"],
    "transaction_date": ["transaction_date", "Transaction Date", "Date"],
    "value_date": ["value_date", "Value Date"],
    "currency": ["currency", "Currency"],
    "amount": ["amount", "Amount", "Credit"],
    "direction": ["direction", "Direction", "Type"],
    "counterparty": ["counterparty", "Counterparty", "Payor", "Payer"],
    "reference": ["reference", "Reference", "Payment Reference"],
    "description": ["description", "Description", "Memo", "Narrative"],
}


@dataclass(frozen=True)
class ReconciliationConfig:
    amount_tolerance: Decimal = Decimal("0.01")
    date_window_days: int = 5
    currency_required: bool = True
    allow_many_to_one: bool = False
    settlement_fields: dict[str, list[str]] = field(default_factory=lambda: DEFAULT_SETTLEMENT_FIELDS.copy())
    bank_fields: dict[str, list[str]] = field(default_factory=lambda: DEFAULT_BANK_FIELDS.copy())

    @classmethod
    def load(cls, path: str | Path | None = None) -> "ReconciliationConfig":
        config = cls()
        if path is None:
            return config

        data = _load_mapping(Path(path))
        settlement_fields = _merge_fields(config.settlement_fields, data.get("settlement_fields", {}))
        bank_fields = _merge_fields(config.bank_fields, data.get("bank_fields", {}))

        return cls(
            amount_tolerance=Decimal(str(data.get("amount_tolerance", config.amount_tolerance))),
            date_window_days=int(data.get("date_window_days", config.date_window_days)),
            currency_required=bool(data.get("currency_required", config.currency_required)),
            allow_many_to_one=bool(data.get("allow_many_to_one", config.allow_many_to_one)),
            settlement_fields=settlement_fields,
            bank_fields=bank_fields,
        )

    def with_overrides(
        self,
        amount_tolerance: str | None = None,
        date_window_days: int | None = None,
    ) -> "ReconciliationConfig":
        return ReconciliationConfig(
            amount_tolerance=Decimal(str(amount_tolerance)) if amount_tolerance is not None else self.amount_tolerance,
            date_window_days=date_window_days if date_window_days is not None else self.date_window_days,
            currency_required=self.currency_required,
            allow_many_to_one=self.allow_many_to_one,
            settlement_fields=self.settlement_fields,
            bank_fields=self.bank_fields,
        )


def _merge_fields(defaults: dict[str, list[str]], overrides: dict[str, Any]) -> dict[str, list[str]]:
    merged = {key: list(value) for key, value in defaults.items()}
    for key, value in overrides.items():
        if isinstance(value, str):
            merged[key] = [value]
        elif isinstance(value, list):
            merged[key] = [str(item) for item in value]
        else:
            raise ConfigError(f"field mapping for {key!r} must be a string or list")
    return merged


def _load_mapping(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise ConfigError(f"config file not found: {path}")

    text = path.read_text(encoding="utf-8")
    if path.suffix.lower() == ".json":
        import json

        loaded = json.loads(text)
        if not isinstance(loaded, dict):
            raise ConfigError("JSON config must be an object")
        return loaded

    try:
        import yaml  # type: ignore[import-not-found]
    except ImportError:
        return _parse_minimal_yaml(text)

    loaded = yaml.safe_load(text) or {}
    if not isinstance(loaded, dict):
        raise ConfigError("YAML config must be a mapping")
    return loaded


def _parse_minimal_yaml(text: str) -> dict[str, Any]:
    """Parse the small YAML subset used by examples without requiring PyYAML."""

    result: dict[str, Any] = {}
    current_section: str | None = None

    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue

        if not line.startswith(" ") and stripped.endswith(":"):
            current_section = stripped[:-1]
            result[current_section] = {}
            continue

        if ":" not in stripped:
            raise ConfigError("install PyYAML for advanced YAML config syntax")

        key, raw_value = stripped.split(":", 1)
        value = _parse_scalar_or_list(raw_value.strip())
        if line.startswith(" ") and current_section:
            result[current_section][key.strip()] = value
        else:
            current_section = None
            result[key.strip()] = value

    return result


def _parse_scalar_or_list(value: str) -> Any:
    if value.startswith("[") and value.endswith("]"):
        inner = value[1:-1].strip()
        if not inner:
            return []
        return [item.strip().strip("'\"") for item in inner.split(",")]
    lowered = value.lower()
    if lowered in {"true", "false"}:
        return lowered == "true"
    return value.strip("'\"")

