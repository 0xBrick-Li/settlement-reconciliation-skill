class ReconciliationError(Exception):
    """Base error for reconciliation failures."""


class ConfigError(ReconciliationError):
    """Raised when configuration cannot be loaded or validated."""


class LoadError(ReconciliationError):
    """Raised when an input file cannot be loaded."""


class NormalizationError(ReconciliationError):
    """Raised when a required row cannot be normalized."""

