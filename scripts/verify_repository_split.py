"""Executes the Phase 7 repository-split acceptance test end to end.

See ATMANATIC_REPOSITORY_BOUNDARY_PLAN.md "Final acceptance test" and
ATMANATIC_MASTER_IMPLEMENTATION_ROADMAP.md Step 6. This script only creates and
deletes a throwaway temporary directory outside the repository; it never
modifies the Atmanatic repository itself and is safe to re-run.

It proves, rather than asserts, that:
1. a consumer can install the built wheel into an isolated target directory
   and use it with the Atmanatic source tree absent from `sys.path` and the
   working directory;
2. the consumer cannot reach the source tree through the installed package;
3. Atmanatic's own test suite still passes with no awareness that a consumer
   ever existed.

A full throwaway virtual environment was tried first but its `ensurepip`
bootstrap step made the check too slow/network-dependent for routine use;
installing the wheel into a plain `--target` directory and running the
consumer with `PYTHONPATH` limited to that directory proves the same
boundary (no source tree on `sys.path`) without that cost.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

CONSUMER_SMOKE_TEST = '''
import sys
from pathlib import Path

repo_root = Path(r"{repo_root}")
assert repo_root not in [Path(p).resolve() for p in sys.path if p], (
    "consumer must not have the Atmanatic repository on sys.path"
)

import atmanatic_research as ar

installed_from = Path(ar.__file__).resolve()
assert repo_root not in installed_from.parents, (
    f"atmanatic_research was imported from the source tree: {{installed_from}}"
)

record = {{
    "schema_version": 1,
    "artifact_id": "consumer-smoke-1",
    "parent_artifact_ids": [],
    "producer": "external-consumer",
    "created_at": "2026-09-18T00:00:00+00:00",
    "content_hash": "a" * 64,
    "execution_authorized": False,
}}
ar.validate_artifact_lineage(record)

try:
    ar.validate_artifact_lineage({{**record, "execution_authorized": True}})
    raise SystemExit("consumer smoke test failed: authority claim was not rejected")
except ar.ArtifactContractError:
    pass

print("CONSUMER_SMOKE_TEST_OK", installed_from)
'''


def _run(cmd: list[str], **kwargs) -> None:
    print("+", " ".join(str(part) for part in cmd))
    subprocess.run(cmd, check=True, **kwargs)


def _run_consumer_side(workdir: Path) -> None:
    dist_dir = workdir / "dist"
    install_dir = workdir / "install"

    print(f"== building wheel into isolated dist dir: {dist_dir}")
    _run([sys.executable, "-m", "pip", "wheel", str(REPO_ROOT), "-w", str(dist_dir), "--no-deps"])
    wheels = list(dist_dir.glob("atmanatic_research-*.whl"))
    if not wheels:
        raise SystemExit("no wheel was produced")
    wheel = wheels[0]
    print(f"== built {wheel.name}")

    print(f"== installing wheel into isolated target directory: {install_dir}")
    _run(
        [sys.executable, "-m", "pip", "install", "--no-index", "--no-deps", "--target", str(install_dir), str(wheel)]
    )

    smoke_test_path = workdir / "consumer_smoke_test.py"
    smoke_test_path.write_text(CONSUMER_SMOKE_TEST.format(repo_root=str(REPO_ROOT)), encoding="utf-8")

    print("== running consumer smoke test with cwd outside the repository, "
          "PYTHONPATH limited to the installed target directory")
    consumer_env = {"PATH": os.environ.get("PATH", ""), "SYSTEMROOT": os.environ.get("SYSTEMROOT", ""), "PYTHONPATH": str(install_dir)}
    result = subprocess.run(
        [sys.executable, str(smoke_test_path)],
        cwd=str(workdir),
        capture_output=True,
        text=True,
        env=consumer_env,
    )
    print(result.stdout)
    if result.stderr:
        print(result.stderr, file=sys.stderr)
    if result.returncode != 0:
        raise SystemExit("consumer smoke test failed")


def main() -> int:
    workdir = Path(tempfile.mkdtemp(prefix="atmanatic-split-check-"))
    try:
        _run_consumer_side(workdir)
    finally:
        shutil.rmtree(workdir, ignore_errors=True)
        print(f"== deleted throwaway consumer environment: {workdir}")

    print("== confirming Atmanatic's own tests still pass with the consumer gone")
    _run([sys.executable, "-m", "unittest", "discover", "-s", "tests", "-q"], cwd=str(REPO_ROOT))
    print("== ACCEPTANCE TEST PASSED: consumer worked with the source tree absent, "
          "and Atmanatic's tests pass with the consumer absent")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
