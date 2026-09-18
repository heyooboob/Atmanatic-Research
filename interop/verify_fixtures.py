"""Verifies that fixtures in `interop/fixtures/` match the reference implementation's
actual current behavior.

This is the Python side of the interoperability harness described in
ATMANATIC_PROTOCOL_0.1_DRAFT.md section 14. A second, independent
implementation is expected to load the same fixture files and reproduce the
same verdict and error code for every case; this script only proves the
Python reference implementation agrees with its own generated fixtures (catches
drift if a validator changes without regenerating fixtures).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from interop.generate_fixtures import CASE_SUITES, FIXTURES_DIR, _actual_verdict  # noqa: E402


class FixtureDriftError(RuntimeError):
    """Raised when a committed fixture no longer matches validator behavior."""


def verify() -> int:
    manifest_path = FIXTURES_DIR / "manifest.json"
    if not manifest_path.exists():
        raise FixtureDriftError("no manifest found; run interop/generate_fixtures.py first")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    checked = 0
    for entry in manifest:
        fixture_path = FIXTURES_DIR / entry["path"]
        fixture = json.loads(fixture_path.read_text(encoding="utf-8"))
        validator, _ = CASE_SUITES[fixture["artifact_type"]]
        actual_verdict, actual_code = _actual_verdict(validator, fixture["input"])
        expected = fixture["expected"]
        if actual_verdict != expected["verdict"]:
            raise FixtureDriftError(
                f"fixture '{fixture['case_id']}' has drifted: expected verdict "
                f"'{expected['verdict']}' but validator now returns '{actual_verdict}'"
            )
        if expected["verdict"] == "reject" and expected.get("error_code") is not None:
            if actual_code != expected["error_code"]:
                raise FixtureDriftError(
                    f"fixture '{fixture['case_id']}' has drifted: expected error_code "
                    f"'{expected['error_code']}' but validator now raises '{actual_code}'"
                )
        checked += 1
    return checked


def collect_results() -> list[dict[str, object]]:
    """Return per-fixture actual verdict/code, for report generation.

    Unlike `verify()`, this never raises on drift; it reports what actually
    happened so a report can show disagreement instead of crashing on it.
    """
    manifest_path = FIXTURES_DIR / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    results: list[dict[str, object]] = []
    for entry in manifest:
        fixture_path = FIXTURES_DIR / entry["path"]
        fixture = json.loads(fixture_path.read_text(encoding="utf-8"))
        validator, _ = CASE_SUITES[fixture["artifact_type"]]
        actual_verdict, actual_code = _actual_verdict(validator, fixture["input"])
        results.append(
            {
                "case_id": fixture["case_id"],
                "artifact_type": fixture["artifact_type"],
                "expected_verdict": fixture["expected"]["verdict"],
                "expected_code": fixture["expected"].get("error_code"),
                "actual_verdict": actual_verdict,
                "actual_code": actual_code,
            }
        )
    return results


def main() -> int:
    checked = verify()
    print(f"verified {checked} fixtures against the reference implementation with zero drift")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
