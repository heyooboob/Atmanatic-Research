"""Shared append-only JSON-lines file I/O for local, caller-supplied paths.

Both `validity_protocol.store.PacketStore` and
`atmanatic_research.lifecycle_events.LifecycleEventLog` persist different
records but need the same low-level guarantees: create the parent directory,
append one JSON object per line, and read every line back in file order. This
module owns only that mechanical behavior; it has no opinion about what a
record means or whether it is valid.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable


class JsonLinesLog:
    """Append-only JSON-lines file at a caller-supplied path."""

    def __init__(self, path: Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def append_record(
        self, record: dict[str, Any], *, default: Callable[[Any], Any] | None = None, sort_keys: bool = False
    ) -> None:
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, default=default, sort_keys=sort_keys) + "\n")

    def read_all(self) -> list[dict[str, Any]]:
        if not self.path.exists():
            return []
        records: list[dict[str, Any]] = []
        with self.path.open("r", encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if line:
                    records.append(json.loads(line))
        return records
