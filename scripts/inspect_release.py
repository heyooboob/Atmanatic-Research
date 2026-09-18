"""Inspects a built wheel for release hygiene: contents, hash, and package scope.

Implements the mechanical part of Phase 8 (ATMANATIC_VERIFIABLE_AGENTIC_RESEARCH_IMPLEMENTATION_PLAN.md
section 13): a release must be reproducible from a tagged revision, its
artifact hash known, and its contents inspectable before anyone trusts it.
This does not sign releases or publish anything; it only builds, hashes, and
fails closed if the wheel contains anything outside the declared package
scope.
"""

from __future__ import annotations

import hashlib
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
ALLOWED_TOP_LEVEL_PACKAGES = ("atmanatic_research", "validity_protocol")


class ReleaseInspectionError(RuntimeError):
    """Raised when a built wheel violates release hygiene rules."""


def build_wheel(dist_dir: Path) -> Path:
    """Build the wheel from `REPO_ROOT` into `dist_dir` and return its path."""
    subprocess.run(
        [sys.executable, "-m", "pip", "wheel", str(REPO_ROOT), "-w", str(dist_dir), "--no-deps"],
        check=True,
    )
    wheels = sorted(dist_dir.glob("atmanatic_research-*.whl"))
    if not wheels:
        raise ReleaseInspectionError("no wheel was produced")
    return wheels[-1]


def hash_wheel(wheel_path: Path) -> str:
    """Return the SHA-256 hex digest of the wheel's exact bytes."""
    digest = hashlib.sha256()
    with wheel_path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def inspect_wheel_contents(wheel_path: Path) -> list[str]:
    """Return the wheel's member names, failing closed on out-of-scope content.

    Every top-level Python package member must belong to
    `ALLOWED_TOP_LEVEL_PACKAGES`, and no member may reference a parent
    directory or an absolute path.
    """
    with zipfile.ZipFile(wheel_path) as archive:
        names = archive.namelist()

    for name in names:
        if name.startswith("/") or ".." in Path(name).parts:
            raise ReleaseInspectionError(f"wheel member escapes its archive root: {name}")

    disallowed = []
    for name in names:
        top_level = name.split("/", 1)[0]
        if top_level.endswith(".dist-info") or top_level.endswith(".data"):
            continue
        package_name = top_level.split(".")[0]
        if package_name not in ALLOWED_TOP_LEVEL_PACKAGES:
            disallowed.append(name)
    if disallowed:
        raise ReleaseInspectionError(
            "wheel contains members outside the declared package scope: " + ", ".join(disallowed)
        )
    return names


def inspect_release() -> dict[str, object]:
    """Build, hash, and inspect the current tree's wheel; return a summary record."""
    with tempfile.TemporaryDirectory(prefix="atmanatic-release-inspect-") as tmp:
        dist_dir = Path(tmp)
        wheel_path = build_wheel(dist_dir)
        content_hash = hash_wheel(wheel_path)
        members = inspect_wheel_contents(wheel_path)
        return {
            "wheel_name": wheel_path.name,
            "sha256": content_hash,
            "member_count": len(members),
            "top_level_packages": sorted(
                {name.split("/", 1)[0] for name in members if "/" in name or name.endswith(".py")}
            ),
        }


def main() -> int:
    summary = inspect_release()
    print(f"wheel: {summary['wheel_name']}")
    print(f"sha256: {summary['sha256']}")
    print(f"members: {summary['member_count']}")
    print("top-level entries:", ", ".join(summary["top_level_packages"]))
    print("RELEASE_INSPECTION_PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
