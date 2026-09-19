"""Digital signatures and key lifecycle for released Atmanatic artifacts.

Signing covers exactly the canonical projection `compute_content_hash` also
hashes (`content_hash` and any prior `signature` excluded from the signed
bytes), so a signature can never silently diverge from the hash it
accompanies; both are independently verifiable derivations of the same
substantive fields.

Key identity is derived, not asserted: `key_id` is the SHA-256 hex digest of
the raw public key bytes, so two records can never disagree about which key
they mean while attaching different labels to it.

Requires the optional `cryptography` dependency
(`pip install atmanatic-research[signing]`); the core package stays
dependency-free without it, and every function here raises a clear
`SigningError` if it is missing rather than failing with an import traceback
deep in a call stack.
"""

from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from typing import Any

from .canonical import canonical_json_bytes, project_for_hash
from .error_codes import (
    ContractError,
    INVALID_STATE_TRANSITION,
    MISSING_OR_INVALID_FIELD,
    UNSUPPORTED_VERSION,
)
from .timestamps import TimestampError, parse_rfc3339
from validity_protocol.jsonl import JsonLinesLog

try:
    from cryptography.exceptions import InvalidSignature
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey
except ImportError as _import_error:  # pragma: no cover - exercised only without the extra installed
    Ed25519PrivateKey = None  # type: ignore[assignment,misc]
    Ed25519PublicKey = None  # type: ignore[assignment,misc]
    InvalidSignature = Exception  # type: ignore[assignment,misc]
    _CRYPTOGRAPHY_IMPORT_ERROR: ImportError | None = _import_error
else:
    _CRYPTOGRAPHY_IMPORT_ERROR = None

KEY_RECORD_SCHEMA_VERSION = 1
SIGNING_ALGORITHMS = frozenset({"ed25519"})
KEY_STATUSES = frozenset({"active", "revoked"})
KEY_REVOCATION_REASONS = frozenset({"compromised", "superseded", "no_longer_used", "policy_violation"})


class SigningError(ContractError):
    """Raised for malformed signing/key-record inputs, unsupported algorithms, or bad transitions."""


def _require_cryptography() -> None:
    if _CRYPTOGRAPHY_IMPORT_ERROR is not None:
        raise SigningError(
            "the 'cryptography' package is required for signing; install with "
            "'pip install atmanatic-research[signing]'",
            code=MISSING_OR_INVALID_FIELD,
        ) from _CRYPTOGRAPHY_IMPORT_ERROR


def _require_supported_algorithm(algorithm: str) -> None:
    if algorithm not in SIGNING_ALGORITHMS:
        raise SigningError(f"unsupported signing algorithm: {algorithm!r}", code=UNSUPPORTED_VERSION)


def key_id_for_public_key(public_key_bytes: bytes) -> str:
    """Derive the stable key_id from raw public key bytes; identity is never self-asserted."""
    return hashlib.sha256(public_key_bytes).hexdigest()


def public_key_from_private_key(private_key_bytes: bytes, *, algorithm: str = "ed25519") -> bytes:
    """Derive the raw public key bytes for a private key; a release pipeline never stores public keys separately."""
    _require_cryptography()
    _require_supported_algorithm(algorithm)
    private_key = Ed25519PrivateKey.from_private_bytes(private_key_bytes)
    return private_key.public_key().public_bytes_raw()


def generate_signing_key(*, algorithm: str = "ed25519") -> tuple[bytes, bytes]:
    """Generate a new `(private_key_bytes, public_key_bytes)` pair for `algorithm`."""
    _require_cryptography()
    _require_supported_algorithm(algorithm)
    private_key = Ed25519PrivateKey.generate()
    private_bytes = private_key.private_bytes_raw()
    public_bytes = private_key.public_key().public_bytes_raw()
    return private_bytes, public_bytes


def sign_record(
    record: dict[str, Any], *, private_key_bytes: bytes, key_id: str, algorithm: str = "ed25519"
) -> dict[str, Any]:
    """Return a copy of `record` with a `signature` field over its canonical projection."""
    _require_cryptography()
    _require_supported_algorithm(algorithm)
    message = canonical_json_bytes(project_for_hash(record))
    private_key = Ed25519PrivateKey.from_private_bytes(private_key_bytes)
    signature_bytes = private_key.sign(message)
    signed = dict(record)
    signed["signature"] = {"key_id": key_id, "algorithm": algorithm, "value": signature_bytes.hex()}
    return signed


def verify_record_signature(record: dict[str, Any], *, public_key_bytes: bytes) -> bool:
    """Return whether `record["signature"]` is valid over the record's canonical projection."""
    _require_cryptography()
    signature = record.get("signature") if isinstance(record, dict) else None
    if not isinstance(signature, dict):
        return False
    algorithm = signature.get("algorithm")
    value = signature.get("value")
    if algorithm not in SIGNING_ALGORITHMS or not isinstance(value, str):
        return False
    try:
        signature_bytes = bytes.fromhex(value)
    except ValueError:
        return False
    if signature.get("key_id") != key_id_for_public_key(public_key_bytes):
        return False
    message = canonical_json_bytes(project_for_hash(record))
    public_key = Ed25519PublicKey.from_public_bytes(public_key_bytes)
    try:
        public_key.verify(signature_bytes, message)
    except InvalidSignature:
        return False
    return True


def _timestamp(value: Any, key: str) -> None:
    try:
        parse_rfc3339(value, key)
    except TimestampError as error:
        raise SigningError(str(error), code=MISSING_OR_INVALID_FIELD) from error


def validate_key_record(record: dict[str, Any]) -> dict[str, Any]:
    """Validate a key lifecycle record's shape, derived identity, and status invariants."""
    if not isinstance(record, dict):
        raise SigningError("key record must be an object", code=MISSING_OR_INVALID_FIELD)
    if record.get("schema_version") != KEY_RECORD_SCHEMA_VERSION:
        raise SigningError(f"schema_version must be {KEY_RECORD_SCHEMA_VERSION}", code=UNSUPPORTED_VERSION)
    key_id = record.get("key_id")
    if not isinstance(key_id, str) or not key_id.strip():
        raise SigningError("key_id must be a non-empty string", code=MISSING_OR_INVALID_FIELD)
    _require_supported_algorithm(record.get("algorithm"))
    public_key = record.get("public_key")
    if not isinstance(public_key, str) or not public_key.strip():
        raise SigningError("public_key must be a non-empty hex string", code=MISSING_OR_INVALID_FIELD)
    try:
        raw_public_key = bytes.fromhex(public_key)
    except ValueError as error:
        raise SigningError("public_key must be valid hex", code=MISSING_OR_INVALID_FIELD) from error
    if key_id_for_public_key(raw_public_key) != key_id:
        raise SigningError("key_id must be the SHA-256 digest of public_key", code=MISSING_OR_INVALID_FIELD)
    if not isinstance(record.get("producer"), str) or not record["producer"].strip():
        raise SigningError("producer must be a non-empty string", code=MISSING_OR_INVALID_FIELD)
    _timestamp(record.get("created_at"), "created_at")
    status = record.get("status")
    if status not in KEY_STATUSES:
        raise SigningError(
            f"status must be one of: {', '.join(sorted(KEY_STATUSES))}", code=MISSING_OR_INVALID_FIELD
        )
    if status == "revoked":
        if record.get("revocation_reason") not in KEY_REVOCATION_REASONS:
            raise SigningError(
                f"revocation_reason must be one of: {', '.join(sorted(KEY_REVOCATION_REASONS))}",
                code=MISSING_OR_INVALID_FIELD,
            )
        _timestamp(record.get("revoked_at"), "revoked_at")
    elif record.get("revoked_at") is not None or record.get("revocation_reason") is not None:
        raise SigningError(
            "only a revoked key may carry revoked_at/revocation_reason", code=MISSING_OR_INVALID_FIELD
        )
    return record


def build_key_record(
    *, public_key_bytes: bytes, producer: str, algorithm: str = "ed25519", created_at: datetime | None = None
) -> dict[str, Any]:
    """Build a validated, active key record; identity is derived from the public key itself."""
    record = {
        "schema_version": KEY_RECORD_SCHEMA_VERSION,
        "key_id": key_id_for_public_key(public_key_bytes),
        "algorithm": algorithm,
        "public_key": public_key_bytes.hex(),
        "producer": producer,
        "created_at": (created_at or datetime.now(timezone.utc)).isoformat(),
        "status": "active",
        "revoked_at": None,
        "revocation_reason": None,
    }
    return validate_key_record(record)


def _event_time(event: dict[str, Any]) -> str:
    return event.get("revoked_at") or event["created_at"]


class KeyRegistry:
    """Append-only registry of key lifecycle events (registration and revocation).

    Separate from execution authority: this registry decides only whether a
    key is presently active, never whether a signed artifact may act.
    """

    def __init__(self, path):
        self._log = JsonLinesLog(path)

    @property
    def path(self):
        return self._log.path

    def register(self, key_record: dict[str, Any]) -> dict[str, Any]:
        validated = validate_key_record(key_record)
        if validated["status"] != "active":
            raise SigningError("only an active key record may be registered", code=MISSING_OR_INVALID_FIELD)
        if validated["key_id"] in self.latest_status():
            raise SigningError(f"key {validated['key_id']} is already registered", code=INVALID_STATE_TRANSITION)
        self._log.append_record(validated, sort_keys=True)
        return validated

    def revoke(self, key_id: str, *, reason: str, revoked_at: datetime | None = None) -> dict[str, Any]:
        if reason not in KEY_REVOCATION_REASONS:
            raise SigningError(
                f"reason must be one of: {', '.join(sorted(KEY_REVOCATION_REASONS))}",
                code=MISSING_OR_INVALID_FIELD,
            )
        current = self.latest_status().get(key_id)
        if current is None:
            raise SigningError(f"unknown key_id: {key_id}", code=MISSING_OR_INVALID_FIELD)
        if current["status"] == "revoked":
            raise SigningError(f"key {key_id} is already revoked", code=INVALID_STATE_TRANSITION)
        event = dict(current)
        event["status"] = "revoked"
        event["revoked_at"] = (revoked_at or datetime.now(timezone.utc)).isoformat()
        event["revocation_reason"] = reason
        validated = validate_key_record(event)
        self._log.append_record(validated, sort_keys=True)
        return validated

    def read_all(self) -> list[dict[str, Any]]:
        return self._log.read_all()

    def latest_status(self) -> dict[str, dict[str, Any]]:
        """Return the most recent event per key, keyed by `key_id`, resolved by event recency."""
        latest: dict[str, dict[str, Any]] = {}
        for event in self.read_all():
            key = event["key_id"]
            current = latest.get(key)
            if current is None or _event_time(event) >= _event_time(current):
                latest[key] = event
        return latest

    def is_active(self, key_id: str) -> bool:
        status = self.latest_status().get(key_id)
        return status is not None and status["status"] == "active"


def verify_signed_record_with_registry(record: dict[str, Any], registry: KeyRegistry) -> bool:
    """Verify a record's signature AND that its signing key is currently active (not revoked).

    A revoked key can never validate a record going forward, even one it
    validly signed while active.
    """
    signature = record.get("signature") if isinstance(record, dict) else None
    if not isinstance(signature, dict):
        return False
    key_status = registry.latest_status().get(signature.get("key_id"))
    if key_status is None or key_status["status"] != "active":
        return False
    return verify_record_signature(record, public_key_bytes=bytes.fromhex(key_status["public_key"]))
