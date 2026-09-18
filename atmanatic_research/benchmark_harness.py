"""Deterministic benchmark harness for validator regression gates.

Runs a fixed, content-hashed fixture corpus against real validators and
reports component metrics separately, per the implementation plan's Phase 4
guidance. No composite score is produced: false-accept rate, false-reject
rate, and reproducibility are tracked independently.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Any, Callable, Mapping, Sequence

from .canonical import canonical_json_bytes
from .error_codes import ContractError

BENCHMARK_SCHEMA_VERSION = 1


class BenchmarkHarnessError(ValueError):
    """Raised when a benchmark case or validator registry is malformed."""


@dataclass(frozen=True)
class BenchmarkCase:
    case_id: str
    validator_name: str
    input: Any
    expected: str
    expected_code: str | None = None

    def __post_init__(self) -> None:
        if self.expected not in ("accept", "reject"):
            raise BenchmarkHarnessError(f"case '{self.case_id}' expected must be 'accept' or 'reject'")


def _run_case(case: BenchmarkCase, validators: Mapping[str, Callable[[Any], Any]]) -> dict[str, Any]:
    validator = validators.get(case.validator_name)
    if validator is None:
        raise BenchmarkHarnessError(
            f"case '{case.case_id}' references unknown validator '{case.validator_name}'"
        )

    actual_code = None
    try:
        validator(case.input)
        actual = "accept"
    except ContractError as error:
        actual = "reject"
        actual_code = error.code
    except ValueError:
        actual = "reject"

    passed = actual == case.expected
    if passed and case.expected == "reject" and case.expected_code is not None:
        passed = actual_code == case.expected_code

    return {
        "case_id": case.case_id,
        "validator_name": case.validator_name,
        "expected": case.expected,
        "expected_code": case.expected_code,
        "actual": actual,
        "actual_code": actual_code,
        "passed": passed,
    }


def run_benchmark(
    cases: Sequence[BenchmarkCase],
    validators: Mapping[str, Callable[[Any], Any]],
    *,
    benchmark_id: str,
    processor_version: str,
) -> dict[str, Any]:
    """Run `cases` against `validators` and return a `validate_benchmark`-conformant record.

    The corpus is executed twice; a run that is not byte-identical across
    repetitions raises rather than silently reporting a flaky pass.
    """
    if not cases:
        raise BenchmarkHarnessError("cases must be a non-empty sequence")

    first_pass = [_run_case(case, validators) for case in cases]
    second_pass = [_run_case(case, validators) for case in cases]
    if first_pass != second_pass:
        raise BenchmarkHarnessError("benchmark run is not reproducible across repeated execution")

    reject_expected = [result for result in first_pass if result["expected"] == "reject"]
    accept_expected = [result for result in first_pass if result["expected"] == "accept"]
    false_accepts = [result for result in reject_expected if result["actual"] == "accept"]
    false_rejects = [result for result in accept_expected if result["actual"] == "reject"]

    metrics = {
        "case_count": len(first_pass),
        "false_accept_rate": (len(false_accepts) / len(reject_expected)) if reject_expected else 0.0,
        "false_reject_rate": (len(false_rejects) / len(accept_expected)) if accept_expected else 0.0,
        "reproducible": True,
    }

    fixture_hash = hashlib.sha256(
        canonical_json_bytes(
            [
                {
                    "case_id": case.case_id,
                    "validator_name": case.validator_name,
                    "input": case.input,
                    "expected": case.expected,
                }
                for case in cases
            ]
        )
    ).hexdigest()

    return {
        "schema_version": BENCHMARK_SCHEMA_VERSION,
        "execution_authorized": False,
        "trust_boundary": {"untrusted_embedded": False, "execution_authorized": False},
        "benchmark": benchmark_id,
        "fixture_hash": fixture_hash,
        "processor_version": processor_version,
        "metrics": metrics,
        "cases": first_pass,
    }
