"""Scans declared dependencies for known vulnerabilities using pip-audit.

Implements the dependency/vulnerability scanning deliverable of Phase 8
(ATMANATIC_VERIFIABLE_AGENTIC_RESEARCH_IMPLEMENTATION_PLAN.md section 13). The
package declares zero required runtime dependencies and one optional extra
(`cryptography`, via the `signing` extra); this scans whatever is actually
installed in the current environment. A missing scanner fails closed rather
than being silently reported as a clean scan.
"""

from __future__ import annotations

import importlib.util
import subprocess
import sys


class DependencyScanError(RuntimeError):
    """Raised when the dependency scan cannot run, or finds a known vulnerability."""


def _require_pip_audit() -> None:
    if importlib.util.find_spec("pip_audit") is None:
        raise DependencyScanError(
            "pip-audit is not installed; install it with 'pip install pip-audit' "
            "before running a dependency scan (a missing scanner is never treated "
            "as a clean scan)"
        )


def scan_dependencies() -> str:
    """Run pip-audit against the current environment; return its output, or raise on any finding."""
    _require_pip_audit()
    result = subprocess.run(
        [sys.executable, "-m", "pip_audit", "--strict", "--progress-spinner", "off"],
        capture_output=True,
        text=True,
    )
    output = result.stdout + result.stderr
    if result.returncode != 0:
        raise DependencyScanError(f"pip-audit reported a finding or failure (exit code {result.returncode}):\n{output}")
    return output


def main() -> int:
    try:
        output = scan_dependencies()
    except DependencyScanError as error:
        print(f"DEPENDENCY_SCAN_FAILED: {error}", file=sys.stderr)
        return 1
    print(output)
    print("DEPENDENCY_SCAN_PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
