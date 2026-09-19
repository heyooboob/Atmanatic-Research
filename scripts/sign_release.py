"""Signs a release manifest binding a tag and wheel hash to a registered signing key.

Implements the "signing in CI" deliverable of Phase 8
(ATMANATIC_VERIFIABLE_AGENTIC_RESEARCH_IMPLEMENTATION_PLAN.md section 13). The
signed artifact is a non-authorizing manifest record
(`execution_authorized: false`): it only attests which exact wheel bytes a
given tagged revision produced, under a key that is registered and active in
`release/keys.jsonl`. See RELEASE_RUNBOOK.md for the end-to-end release and
rollback procedure, including how to bootstrap that registry.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from atmanatic_research import (  # noqa: E402
    KeyRegistry,
    compute_content_hash,
    key_id_for_public_key,
    public_key_from_private_key,
    sign_record,
)
from inspect_release import hash_wheel, inspect_release, inspect_wheel_contents  # noqa: E402

DEFAULT_KEY_REGISTRY_PATH = REPO_ROOT / "release" / "keys.jsonl"
DEFAULT_MANIFEST_PATH = REPO_ROOT / "dist" / "release_manifest.json"
RELEASE_MANIFEST_SCHEMA_VERSION = 1


class SignReleaseError(RuntimeError):
    """Raised when a release cannot be signed: unregistered/revoked key, or bad inputs."""


def build_release_manifest(
    *, tag: str, wheel_summary: dict[str, Any], producer: str, now: datetime | None = None
) -> dict[str, Any]:
    """Build the unsigned, content-hashed release manifest for one tagged wheel build."""
    created_at = now or datetime.now(timezone.utc)
    manifest: dict[str, Any] = {
        "schema_version": RELEASE_MANIFEST_SCHEMA_VERSION,
        "artifact_id": f"release-{tag}-{uuid.uuid4().hex}",
        "parent_artifact_ids": [],
        "producer": producer,
        "created_at": created_at.isoformat(),
        "content_hash": "0" * 64,
        "execution_authorized": False,
        "release_tag": tag,
        "wheel_name": wheel_summary["wheel_name"],
        "wheel_sha256": wheel_summary["sha256"],
    }
    manifest["content_hash"] = compute_content_hash(manifest)
    return manifest


def sign_release(
    *,
    tag: str,
    producer: str,
    private_key_hex: str,
    registry_path: Path = DEFAULT_KEY_REGISTRY_PATH,
    wheel_summary: dict[str, Any] | None = None,
    now: datetime | None = None,
) -> dict[str, Any]:
    """Build and sign a release manifest; fail closed unless the signing key is registered and active."""
    registry = KeyRegistry(registry_path)
    private_key_bytes = bytes.fromhex(private_key_hex)
    public_key_bytes = public_key_from_private_key(private_key_bytes)
    key_id = key_id_for_public_key(public_key_bytes)
    if not registry.is_active(key_id):
        raise SignReleaseError(f"signing key {key_id} is not registered and active in {registry_path}")

    manifest = build_release_manifest(
        tag=tag, wheel_summary=wheel_summary or inspect_release(), producer=producer, now=now
    )
    return sign_record(manifest, private_key_bytes=private_key_bytes, key_id=key_id)


def summarize_wheel(wheel_path: Path) -> dict[str, Any]:
    """Summarize the exact wheel that will be signed and published."""
    members = inspect_wheel_contents(wheel_path)
    return {
        "wheel_name": wheel_path.name,
        "sha256": hash_wheel(wheel_path),
        "member_count": len(members),
        "top_level_packages": sorted(
            {name.split("/", 1)[0] for name in members if "/" in name or name.endswith(".py")}
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tag", required=True, help="the release tag being signed, e.g. v0.1.0")
    parser.add_argument("--producer", default="atmanatic-release-ci")
    parser.add_argument("--registry", type=Path, default=DEFAULT_KEY_REGISTRY_PATH)
    parser.add_argument("--out", type=Path, default=DEFAULT_MANIFEST_PATH)
    parser.add_argument(
        "--wheel",
        type=Path,
        default=None,
        help="sign this already-built wheel instead of building a temporary inspection wheel",
    )
    args = parser.parse_args()

    private_key_hex = os.environ.get("ATMANATIC_RELEASE_PRIVATE_KEY")
    if not private_key_hex:
        print("ATMANATIC_RELEASE_PRIVATE_KEY is not set", file=sys.stderr)
        return 2

    try:
        signed = sign_release(
            tag=args.tag,
            producer=args.producer,
            private_key_hex=private_key_hex,
            registry_path=args.registry,
            wheel_summary=summarize_wheel(args.wheel) if args.wheel is not None else None,
        )
    except SignReleaseError as error:
        print(f"SIGN_RELEASE_FAILED: {error}", file=sys.stderr)
        return 1

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(signed, indent=2, sort_keys=True), encoding="utf-8")
    print(f"SIGN_RELEASE_PASSED: wrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
