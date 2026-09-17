"""Domain-neutral source perimeter and evidence-tier policy evaluation."""

from __future__ import annotations

from datetime import datetime
from typing import Any

TIER_RANK = {"A": 4, "B": 3, "C": 2, "D": 1}
ACCESS_MODES = {"public_anonymous", "public_identified", "api_key", "oauth", "custom"}


class SourcePolicyError(ValueError):
    """Raised when a source request violates the configured perimeter."""


def validate_source_definition(source: dict[str, Any]) -> dict[str, Any]:
    """Validate source access metadata without resolving credentials or making a request."""
    if not isinstance(source, dict):
        raise SourcePolicyError("source definition must be an object")
    if not isinstance(source.get("source_id"), str) or not source["source_id"].strip():
        raise SourcePolicyError("source_id must be a non-empty string")

    access = source.get("access")
    if access is None:
        return source
    if not isinstance(access, dict):
        raise SourcePolicyError("source access policy must be an object")
    mode = access.get("mode")
    if mode not in ACCESS_MODES:
        raise SourcePolicyError(f"Unknown source access mode: {mode}")
    if not isinstance(access.get("policy_version"), str) or not access["policy_version"].strip():
        raise SourcePolicyError("source access policy_version must be a non-empty string")

    if mode == "public_identified":
        identity = access.get("identity")
        if not isinstance(identity, dict):
            raise SourcePolicyError("public_identified access requires an identity policy")
        if identity.get("mechanism") != "header":
            raise SourcePolicyError("public_identified identity mechanism must be 'header'")
        if not isinstance(identity.get("name"), str) or not identity["name"].strip():
            raise SourcePolicyError("request identity header name must be a non-empty string")
        if identity.get("required") is not True:
            raise SourcePolicyError("public_identified request identity must be required")
        if not isinstance(identity.get("profile_id"), str) or not identity["profile_id"].strip():
            raise SourcePolicyError("request identity profile_id must be a non-empty string")

    rate_limit = access.get("rate_limit")
    if rate_limit is not None:
        if not isinstance(rate_limit, dict):
            raise SourcePolicyError("rate_limit must be an object")
        requests = rate_limit.get("requests")
        period_seconds = rate_limit.get("period_seconds")
        if not isinstance(requests, int) or isinstance(requests, bool) or requests <= 0:
            raise SourcePolicyError("rate_limit requests must be a positive integer")
        if not isinstance(period_seconds, (int, float)) or isinstance(period_seconds, bool) or period_seconds <= 0:
            raise SourcePolicyError("rate_limit period_seconds must be positive")
    return source


def assert_request_compliant(
    source: dict[str, Any], request_context: dict[str, Any] | None = None
) -> dict[str, Any]:
    """Check declared request metadata without inspecting secret or personal values."""
    validate_source_definition(source)
    access = source.get("access")
    if not access or access.get("mode") != "public_identified":
        return source
    if not isinstance(request_context, dict):
        raise SourcePolicyError(f"Source '{source['source_id']}' requires request identification")

    identity = access["identity"]
    if request_context.get("identity_profile_id") != identity["profile_id"]:
        raise SourcePolicyError(f"Source '{source['source_id']}' requires identity profile '{identity['profile_id']}'")
    headers = request_context.get("headers_present")
    if not isinstance(headers, list) or not all(isinstance(header, str) for header in headers):
        raise SourcePolicyError("request context headers_present must be a list of strings")
    if identity["name"].casefold() not in {header.casefold() for header in headers}:
        raise SourcePolicyError(f"Source '{source['source_id']}' requires request header '{identity['name']}'")
    return source


def validate_acquisition_receipt(
    receipt: dict[str, Any], *, source: dict[str, Any] | None = None
) -> dict[str, Any]:
    """Validate a non-secret receipt attesting to source-policy-compliant acquisition."""
    if not isinstance(receipt, dict):
        raise SourcePolicyError("acquisition receipt must be an object")
    required_strings = (
        "receipt_id",
        "source_id",
        "retrieved_at",
        "request_policy_version",
        "response_content_hash",
    )
    missing = [field for field in required_strings if not isinstance(receipt.get(field), str) or not receipt[field].strip()]
    if missing:
        raise SourcePolicyError(f"acquisition receipt is missing fields: {', '.join(missing)}")
    try:
        retrieved_at = datetime.fromisoformat(receipt["retrieved_at"].replace("Z", "+00:00"))
    except ValueError as error:
        raise SourcePolicyError("retrieved_at must be a valid ISO timestamp") from error
    if retrieved_at.tzinfo is None:
        raise SourcePolicyError("retrieved_at must include a timezone")
    if receipt.get("identity_requirement_satisfied") is not True:
        raise SourcePolicyError("acquisition receipt must attest that identity requirements were satisfied")

    if source is not None:
        validate_source_definition(source)
        if receipt["source_id"] != source["source_id"]:
            raise SourcePolicyError("acquisition receipt source_id does not match source definition")
        access = source.get("access") or {}
        if access and receipt["request_policy_version"] != access["policy_version"]:
            raise SourcePolicyError("acquisition receipt request_policy_version does not match source policy")
        if access.get("mode") == "public_identified":
            expected_profile = access["identity"]["profile_id"]
            if receipt.get("identity_profile_id") != expected_profile:
                raise SourcePolicyError("acquisition receipt identity_profile_id does not match source policy")
    return receipt


def list_sources(
    registry: dict[str, Any], *, agent: str | None = None, minimum_tier: str | None = None
) -> list[dict[str, Any]]:
    sources = [source for source in registry.get("sources", []) if source.get("enabled", False)]
    if agent:
        sources = [source for source in sources if agent in source.get("allowed_for", [])]
    if minimum_tier:
        required = TIER_RANK.get(minimum_tier.upper())
        if required is None:
            raise SourcePolicyError(f"Unknown source tier: {minimum_tier}")
        sources = [source for source in sources if TIER_RANK.get(source.get("authority_tier"), 0) >= required]
    return sources


def get_source(registry: dict[str, Any], source_id: str) -> dict[str, Any]:
    for source in registry.get("sources", []):
        if source.get("source_id") == source_id and source.get("enabled", False):
            return validate_source_definition(source)
    raise SourcePolicyError(f"Source is not enabled in the institutional registry: {source_id}")


def assert_source_allowed(
    registry: dict[str, Any],
    source_id: str,
    agent: str,
    *,
    minimum_tier: str | None = None,
    request_context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    source = get_source(registry, source_id)
    if agent not in source.get("allowed_for", []):
        raise SourcePolicyError(f"Source '{source_id}' is not approved for agent '{agent}'")
    if minimum_tier and TIER_RANK.get(source.get("authority_tier"), 0) < TIER_RANK.get(minimum_tier.upper(), 99):
        raise SourcePolicyError(f"Source '{source_id}' does not meet minimum tier '{minimum_tier}'")
    return assert_request_compliant(source, request_context)


def evidence_requirement(registry: dict[str, Any], agent: str) -> dict[str, Any]:
    requirement = registry.get("minimum_evidence", {}).get(agent)
    if not requirement:
        raise SourcePolicyError(f"No evidence policy configured for agent '{agent}'")
    return requirement