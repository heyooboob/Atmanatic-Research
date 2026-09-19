"""Verifies a release tag matches the package version declared in pyproject.toml.

Implements the "tag-release checks" deliverable of Phase 8
(ATMANATIC_VERIFIABLE_AGENTIC_RESEARCH_IMPLEMENTATION_PLAN.md section 13): a
release is only as trustworthy as the mapping between its git tag and the
artifact it actually builds. This script never builds or publishes anything;
it only proves the tag names the version the repository actually declares.
"""

from __future__ import annotations

import os
import re
import sys
import tomllib
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
_TAG_PATTERN = re.compile(r"^v(?P<version>\d+\.\d+\.\d+)$")


class ReleaseTagError(ValueError):
    """Raised when a release tag does not match the declared package version."""


def declared_version() -> str:
    """Read `[project].version` from the repository's pyproject.toml."""
    data = tomllib.loads((REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    version = data.get("project", {}).get("version")
    if not isinstance(version, str) or not version.strip():
        raise ReleaseTagError("pyproject.toml is missing [project].version")
    return version


def check_release_tag(tag: str) -> str:
    """Return the version encoded in `tag` if it matches `vMAJOR.MINOR.PATCH` and the declared version."""
    match = _TAG_PATTERN.fullmatch(tag)
    if not match:
        raise ReleaseTagError(f"tag {tag!r} does not match the required 'vMAJOR.MINOR.PATCH' pattern")
    tag_version = match.group("version")
    expected = declared_version()
    if tag_version != expected:
        raise ReleaseTagError(
            f"tag {tag!r} declares version {tag_version!r} but pyproject.toml declares {expected!r}"
        )
    return tag_version


def main(argv: list[str]) -> int:
    tag = argv[0] if argv else os.environ.get("GITHUB_REF_NAME", "")
    if not tag:
        print("no tag supplied: pass a tag argument or set GITHUB_REF_NAME", file=sys.stderr)
        return 2
    try:
        version = check_release_tag(tag)
    except ReleaseTagError as error:
        print(f"RELEASE_TAG_CHECK_FAILED: {error}", file=sys.stderr)
        return 1
    print(f"RELEASE_TAG_CHECK_PASSED: tag {tag} matches declared version {version}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
