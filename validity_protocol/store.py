"""Optional local persistence for validity packets.

No downstream-product dependency; the storage path is always caller-supplied,
never hardcoded to any product's state directory.
"""

from __future__ import annotations

import json
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import Any

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
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def append(self, packet: Any) -> None:
        record = asdict(packet)
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, default=_default) + "\n")

    def read_all(self) -> list[dict]:
        if not self.path.exists():
            return []
        records = []
        with self.path.open("r", encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if line:
                    records.append(json.loads(line))
        return records
