"""Versioned, domain-neutral contracts for research artifacts.

This module intentionally has no dependency on downstream products, wallets, or
execution. External systems may consume these contracts, but do not own them.
"""

from __future__ import annotations

from typing import Any

from .error_codes import (
    ContractError,
    INVALID_STATE_TRANSITION,
    MALFORMED_SYNTAX,
    MISSING_OR_INVALID_FIELD,
    PROHIBITED_AUTHORITY_CLAIM,
    UNSUPPORTED_VERSION,
)

CURRENT_SCHEMA_VERSION = 1
API_V2_SCHEMA_VERSION = 1


class IntelligenceContractError(ContractError):
    """Raised when a research artifact violates its versioned contract."""


def _object(value: Any, name: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise IntelligenceContractError(f"{name} must be an object", code=MALFORMED_SYNTAX)
    return value


def _readonly(record: dict[str, Any]) -> None:
    if record.get("execution_authorized") is not False:
        raise IntelligenceContractError("execution_authorized must be false", code=PROHIBITED_AUTHORITY_CLAIM)


def _version(record: dict[str, Any]) -> None:
    if record.get("schema_version") != CURRENT_SCHEMA_VERSION:
        raise IntelligenceContractError(f"schema_version must be {CURRENT_SCHEMA_VERSION}", code=UNSUPPORTED_VERSION)


def _bounded_list(record: dict[str, Any], key: str) -> list[Any]:
    value = record.get(key)
    if not isinstance(value, list):
        raise IntelligenceContractError(f"{key} must be a list", code=MISSING_OR_INVALID_FIELD)
    return value


def validate_benchmark(record: dict[str, Any]) -> dict[str, Any]:
    record = _object(record, "benchmark")
    _version(record)
    if "execution_authorized" in record and record["execution_authorized"] is not False:
        raise IntelligenceContractError("execution_authorized must be false", code=PROHIBITED_AUTHORITY_CLAIM)
    boundary = _object(record.get("trust_boundary"), "trust_boundary")
    if boundary.get("untrusted_embedded") is not False or boundary.get("execution_authorized") is not False:
        raise IntelligenceContractError("benchmark trust boundary is invalid", code=PROHIBITED_AUTHORITY_CLAIM)
    if not isinstance(record.get("benchmark"), str) or not record["benchmark"]:
        raise IntelligenceContractError("benchmark identifier is required", code=MISSING_OR_INVALID_FIELD)
    if not isinstance(record.get("fixture_hash"), str) or len(record["fixture_hash"]) != 64:
        raise IntelligenceContractError("fixture_hash must be a SHA-256 hex digest", code=MALFORMED_SYNTAX)
    if not isinstance(record.get("processor_version"), str) or not record["processor_version"]:
        raise IntelligenceContractError("processor_version is required", code=MISSING_OR_INVALID_FIELD)
    _object(record.get("metrics"), "metrics")
    _bounded_list(record, "cases")
    return record


def validate_export(record: dict[str, Any]) -> dict[str, Any]:
    record = _object(record, "export")
    _version(record)
    boundary = _object(record.get("trust_boundary"), "trust_boundary")
    if boundary.get("untrusted_excluded") is not True or boundary.get("execution_authorized") is not False:
        raise IntelligenceContractError("export trust boundary is invalid", code=PROHIBITED_AUTHORITY_CLAIM)
    if not isinstance(record.get("processor_version"), str) or not record["processor_version"]:
        raise IntelligenceContractError("processor_version is required", code=MISSING_OR_INVALID_FIELD)
    hashes = record.get("source_hashes")
    if not isinstance(hashes, list) or not all(isinstance(value, str) and len(value) == 64 for value in hashes):
        raise IntelligenceContractError("source_hashes must contain SHA-256 hex digests", code=MALFORMED_SYNTAX)
    _bounded_list(record, "documents")
    _bounded_list(record, "claims")
    _bounded_list(record, "entities")
    return record


def validate_soak(record: dict[str, Any]) -> dict[str, Any]:
    record = _object(record, "soak")
    _version(record)
    _readonly(record)
    checks = _bounded_list(record, "checks")
    if not all(isinstance(check, dict) and isinstance(check.get("passed"), bool) for check in checks):
        raise IntelligenceContractError("soak checks must declare boolean passed values", code=MISSING_OR_INVALID_FIELD)
    if record.get("passed") is not all(check["passed"] for check in checks):
        raise IntelligenceContractError("soak passed state does not match checks", code=INVALID_STATE_TRANSITION)
    return record


def validate_intelligence_collection(record: dict[str, Any]) -> dict[str, Any]:
    record = _object(record, "intelligence collection")
    _readonly(record)
    for key in ("recall", "evidence", "claims"):
        _bounded_list(record, key)
    return record


def validate_api_v2_page(record: dict[str, Any]) -> dict[str, Any]:
    """Validate the bounded v2 intelligence pagination envelope."""
    record = _object(record, "intelligence api response")
    if record.get("schema_version") != API_V2_SCHEMA_VERSION:
        raise IntelligenceContractError("API schema_version is invalid", code=UNSUPPORTED_VERSION)
    _readonly(record)
    pagination = _object(record.get("pagination"), "pagination")
    if not all(isinstance(pagination.get(key), int) for key in ("page", "page_size", "total")):
        raise IntelligenceContractError("pagination fields must be integers", code=MISSING_OR_INVALID_FIELD)
    if pagination["page"] < 1 or pagination["page_size"] < 1 or pagination["total"] < 0:
        raise IntelligenceContractError("pagination bounds are invalid", code=MISSING_OR_INVALID_FIELD)
    _bounded_list(record, "items")
    return record