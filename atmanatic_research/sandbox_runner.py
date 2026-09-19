"""Sandboxed subprocess runner for verification specifications or code.

Enforces a wall-clock timeout on every run and, where the platform provides
the primitive (POSIX `resource` limits), CPU-time and address-space limits on
the spawned subprocess. Ambient proxy environment variables are stripped
before spawning.

This module does NOT provide OS-level network denial, filesystem
confinement, or resource limits on Windows: those require an external
sandbox (container, network namespace, firewall, seccomp policy, job
object). Callers that need real network or filesystem isolation MUST run
this behind such an external boundary. Every result's `limits_enforced`
field records exactly which controls this process actually applied, so a
caller can never be misled into believing an unenforced limit held.

`run_verification_in_sandbox()` is the seam a future adapter uses before this
library is ever handed a caller-supplied specification or generated code, per
ATMANATIC_VERIFIABLE_AGENTIC_RESEARCH_IMPLEMENTATION_PLAN.md Phase 5. Nothing
in this repository calls it with untrusted input yet.
"""

from __future__ import annotations

import json
import os
import subprocess
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Sequence

from .artifact_contracts import validate_verification_result
from .canonical import compute_content_hash

try:
    import resource  # POSIX only
except ImportError:  # Windows
    resource = None  # type: ignore[assignment]

# Caps how much stdout/stderr this process will buffer from a subprocess it
# does not trust, independent of any OS-level memory limit on that process.
MAX_CAPTURED_BYTES = 1_000_000

_NETWORK_ENV_KEYS = (
    "http_proxy",
    "https_proxy",
    "no_proxy",
    "HTTP_PROXY",
    "HTTPS_PROXY",
    "NO_PROXY",
    "ALL_PROXY",
    "all_proxy",
)


class SandboxError(ValueError):
    """Raised for programmer errors in sandbox configuration; never for a verifier's own failure."""


@dataclass(frozen=True)
class SandboxLimits:
    wall_clock_seconds: float
    cpu_seconds: float | None = None
    memory_bytes: int | None = None

    def __post_init__(self) -> None:
        if self.wall_clock_seconds <= 0:
            raise SandboxError("wall_clock_seconds must be positive")
        if self.cpu_seconds is not None and self.cpu_seconds <= 0:
            raise SandboxError("cpu_seconds must be positive when set")
        if self.memory_bytes is not None and self.memory_bytes <= 0:
            raise SandboxError("memory_bytes must be positive when set")


@dataclass(frozen=True)
class SandboxResult:
    status: str  # "completed" | "timed_out"
    exit_code: int | None
    stdout: bytes
    stderr: bytes
    stdout_truncated: bool
    stderr_truncated: bool
    wall_time_seconds: float
    limits_enforced: dict[str, bool] = field(default_factory=dict)


def _sandboxed_environment() -> dict[str, str]:
    """A copy of the current environment with ambient proxy variables removed."""
    env = dict(os.environ)
    for key in _NETWORK_ENV_KEYS:
        env.pop(key, None)
    return env


def _preexec_fn(limits: SandboxLimits):
    if resource is None:
        return None

    def _apply() -> None:
        if limits.cpu_seconds is not None:
            cpu_limit = int(limits.cpu_seconds) + 1
            resource.setrlimit(resource.RLIMIT_CPU, (cpu_limit, cpu_limit))
        if limits.memory_bytes is not None:
            resource.setrlimit(resource.RLIMIT_AS, (limits.memory_bytes, limits.memory_bytes))

    return _apply


def run_sandboxed(
    argv: Sequence[str], *, limits: SandboxLimits, cwd: str | None = None, input_bytes: bytes = b""
) -> SandboxResult:
    """Run `argv` as a subprocess under `limits`; never raises for the subprocess's own failure."""
    if not argv:
        raise SandboxError("argv must be a non-empty sequence")

    limits_enforced = {
        "wall_clock": True,
        "cpu": resource is not None and limits.cpu_seconds is not None,
        "memory": resource is not None and limits.memory_bytes is not None,
        "network_denied": False,
    }

    started = time.perf_counter()
    process = subprocess.Popen(
        list(argv),
        cwd=cwd,
        env=_sandboxed_environment(),
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        preexec_fn=_preexec_fn(limits),
    )
    try:
        stdout, stderr = process.communicate(input=input_bytes, timeout=limits.wall_clock_seconds)
        status = "completed"
        exit_code = process.returncode
    except subprocess.TimeoutExpired:
        process.kill()
        stdout, stderr = process.communicate()
        status = "timed_out"
        exit_code = None
    wall_time_seconds = time.perf_counter() - started

    stdout_truncated = len(stdout) > MAX_CAPTURED_BYTES
    stderr_truncated = len(stderr) > MAX_CAPTURED_BYTES
    return SandboxResult(
        status=status,
        exit_code=exit_code,
        stdout=stdout[:MAX_CAPTURED_BYTES],
        stderr=stderr[:MAX_CAPTURED_BYTES],
        stdout_truncated=stdout_truncated,
        stderr_truncated=stderr_truncated,
        wall_time_seconds=wall_time_seconds,
        limits_enforced=limits_enforced,
    )


def _parse_verifier_output(result: SandboxResult) -> tuple[bool, list[str]]:
    """Parse the narrow sandbox verifier protocol: one JSON object with a boolean `ok` field."""
    diagnostics: list[str] = []
    if result.stderr:
        diagnostics.append(f"verifier stderr: {result.stderr.decode('utf-8', errors='replace')[:2000]}")
    if result.stdout_truncated:
        return False, diagnostics + ["verifier stdout exceeded the captured output limit and was rejected"]
    try:
        text = result.stdout.decode("utf-8")
    except UnicodeDecodeError:
        return False, diagnostics + ["verifier stdout was not valid UTF-8"]
    lines = [line for line in text.splitlines() if line.strip()]
    if len(lines) != 1:
        return False, diagnostics + ["verifier stdout must contain exactly one JSON object line"]
    try:
        payload = json.loads(lines[0])
    except json.JSONDecodeError:
        return False, diagnostics + ["verifier stdout was not valid JSON"]
    if not isinstance(payload, dict) or not isinstance(payload.get("ok"), bool):
        return False, diagnostics + ["verifier stdout must be an object with a boolean 'ok' field"]
    verifier_diagnostics = payload.get("diagnostics", [])
    if not isinstance(verifier_diagnostics, list) or not all(
        isinstance(item, str) for item in verifier_diagnostics
    ):
        return False, diagnostics + ["verifier stdout 'diagnostics' must be a list of strings"]
    diagnostics = diagnostics + list(verifier_diagnostics)
    if result.exit_code != 0:
        return False, diagnostics + [f"verifier process exited with non-zero status {result.exit_code}"]
    return bool(payload["ok"]), diagnostics


def run_verification_in_sandbox(
    argv: Sequence[str],
    *,
    verifier_name: str,
    verifier_version: str,
    input_artifact_hash: str,
    specification_ids: list[str],
    environment_id: str,
    limits: SandboxLimits,
    cwd: str | None = None,
    input_bytes: bytes = b"",
    artifact_id: str | None = None,
    now: datetime | None = None,
) -> dict[str, Any]:
    """Run an external verifier subprocess in the sandbox and return a `validate_verification_result` record.

    The subprocess's stdout MUST be exactly one JSON object of the form
    `{"ok": bool, "diagnostics": [str, ...]}` with nothing else on stdout and
    a zero exit code; anything else (empty output, extra output, wrong shape,
    non-JSON, truncated output, non-zero exit) is rejected as malformed and
    recorded as a failed, non-authorizing verification result rather than
    silently accepted.
    """
    result = run_sandboxed(argv, limits=limits, cwd=cwd, input_bytes=input_bytes)

    if result.status == "timed_out":
        status = "timed_out"
        diagnostics = [f"verifier exceeded the wall-clock limit of {limits.wall_clock_seconds}s"]
    else:
        ok, diagnostics = _parse_verifier_output(result)
        status = "verified" if ok else "failed"

    created_at = now or datetime.now(timezone.utc)
    record: dict[str, Any] = {
        "schema_version": 1,
        "artifact_id": artifact_id or f"verification-sandbox-{uuid.uuid4().hex}",
        "parent_artifact_ids": [],
        "producer": verifier_name,
        "created_at": created_at.isoformat(),
        "content_hash": "0" * 64,
        "execution_authorized": False,
        "verifier_name": verifier_name,
        "verifier_version": verifier_version,
        "input_artifact_hash": input_artifact_hash,
        "specification_ids": list(specification_ids),
        "status": status,
        "diagnostics": diagnostics,
        "resource_usage": {
            "wall_time_seconds": round(result.wall_time_seconds, 3),
            "exit_code": result.exit_code,
            "limits_enforced": result.limits_enforced,
        },
        "environment_id": environment_id,
    }
    record["content_hash"] = compute_content_hash(record)
    return validate_verification_result(record)
