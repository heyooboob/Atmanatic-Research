"""Verifies a signed release manifest against the registered key and, optionally, a wheel file.

Used both right after signing (to prove CI produced a verifiable artifact,
not merely a signed one) and during a rollback: confirms a previously
retained release manifest's signature is still traceable to a key that was
active at signing time before restoring that artifact. See
RELEASE_RUNBOOK.md for the full rollback procedure.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from atmanatic_research import verify_content_hash, verify_signed_record_with_registry, KeyRegistry  # noqa: E402
from inspect_release import hash_wheel  # noqa: E402

DEFAULT_KEY_REGISTRY_PATH = REPO_ROOT / "release" / "keys.jsonl"


class ReleaseManifestVerificationError(ValueError):
    """Raised when a release manifest fails hash, signature, or wheel-binding verification."""


def verify_release_manifest(
    manifest: dict, *, registry_path: Path = DEFAULT_KEY_REGISTRY_PATH, wheel_path: Path | None = None
) -> None:
    """Raise `ReleaseManifestVerificationError` unless every check below passes.

    Checks, in order: the manifest's own content hash is intact, its signature
    verifies against a key that is currently active in the registry, and (if
    `wheel_path` is given) the manifest's declared wheel hash matches that
    wheel's actual bytes.
    """
    if not verify_content_hash(manifest):
        raise ReleaseManifestVerificationError("release manifest content_hash does not match its own fields")

    registry = KeyRegistry(registry_path)
    if not verify_signed_record_with_registry(manifest, registry):
        raise ReleaseManifestVerificationError(
            "release manifest signature does not verify against an active registered key"
        )

    if wheel_path is not None:
        actual_hash = hash_wheel(wheel_path)
        if actual_hash.lower() != manifest["wheel_sha256"].lower():
            raise ReleaseManifestVerificationError(
                f"wheel {wheel_path} hash {actual_hash} does not match manifest wheel_sha256 "
                f"{manifest['wheel_sha256']}"
            )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path, help="path to a signed release_manifest.json")
    parser.add_argument("--wheel", type=Path, default=None, help="optional wheel file to bind against")
    parser.add_argument("--registry", type=Path, default=DEFAULT_KEY_REGISTRY_PATH)
    args = parser.parse_args()

    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    try:
        verify_release_manifest(manifest, registry_path=args.registry, wheel_path=args.wheel)
    except ReleaseManifestVerificationError as error:
        print(f"RELEASE_MANIFEST_VERIFICATION_FAILED: {error}", file=sys.stderr)
        return 1

    print(f"RELEASE_MANIFEST_VERIFICATION_PASSED: {args.manifest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
