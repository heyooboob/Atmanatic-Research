"""Shared RFC 3339 timestamp parsing for protocol validators.

Every 0.1 wire timestamp MUST include an explicit UTC offset. Naive
timestamps are rejected rather than silently assumed to be UTC.
"""

from __future__ import annotations

from datetime import datetime


class TimestampError(ValueError):
    """Raised when a value is not a valid RFC 3339 timestamp with an explicit offset."""


def parse_rfc3339(value: object, field: str) -> datetime:
    """Parse `value` as an offset-aware RFC 3339 timestamp or raise `TimestampError`."""
    if not isinstance(value, str) or not value.strip():
        raise TimestampError(f"{field} must be a non-empty timestamp string")
    text = value.strip()
    if text.endswith(("Z", "z")):
        text = f"{text[:-1]}+00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError as error:
        raise TimestampError(f"{field} must be a valid RFC 3339 timestamp") from error
    if parsed.tzinfo is None:
        raise TimestampError(f"{field} must include an explicit UTC offset")
    return parsed
