"""One-time bootstrap: mint a new release signing key and register its public half.

This is a manual maintainer operation, never run in CI. It prints the new
private key once, to be stored only as the `ATMANATIC_RELEASE_PRIVATE_KEY` CI
secret, and appends the corresponding active key record to
`release/keys.jsonl`, which IS committed (it holds only public material and
the append-only revocation history). See RELEASE_RUNBOOK.md.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from atmanatic_research import KeyRegistry, build_key_record, generate_signing_key  # noqa: E402

DEFAULT_KEY_REGISTRY_PATH = REPO_ROOT / "release" / "keys.jsonl"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--producer", required=True, help="the maintainer or role minting this key")
    parser.add_argument("--registry", type=Path, default=DEFAULT_KEY_REGISTRY_PATH)
    args = parser.parse_args()

    private_key_bytes, public_key_bytes = generate_signing_key()
    record = build_key_record(public_key_bytes=public_key_bytes, producer=args.producer)
    registry = KeyRegistry(args.registry)
    registry.register(record)

    print(f"REGISTERED_KEY_ID: {record['key_id']}")
    print(f"registered in: {args.registry}")
    print("Store the line below ONLY as the ATMANATIC_RELEASE_PRIVATE_KEY CI secret.")
    print("It is never written to disk by this script and will not be shown again.")
    print(f"ATMANATIC_RELEASE_PRIVATE_KEY={private_key_bytes.hex()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
