"""Optional local persistence for validity packets.

No downstream-product dependency; the storage path is always caller-supplied,
never hardcoded to any product's state directory.
"""

from __future__ import annotations

from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import Any

from .jsonl import JsonLinesLog
from .levels import ValidityLevel


def _default(value: Any) -> Any:
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, ValidityLevel):
        return value.value
    raise TypeError(f"cannot serialize {type(value)!r}")


class PacketStore:
    """Append-only JSON-lines log of validity packets."""

    def __init__(self, path: Path):
        self._log = JsonLinesLog(path)

    @property
    def path(self) -> Path:
        return self._log.path

    def append(self, packet: Any) -> None:
        self._log.append_record(asdict(packet), default=_default)

    def read_all(self) -> list[dict]:
        return self._log.read_all()
