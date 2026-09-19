"""Lightweight JSON schema for persisted skill run artifacts."""

from __future__ import annotations

from typing import Any

SKILL_RUN_SCHEMA_VERSION = 1

SKILL_RUN_SCHEMA = {
    "type": "object",
    "required": [
        "schema_version",
        "skill_name",
        "skill_version",
        "git_ref",
        "created_at",
        "transcript",
        "observed_actions",
        "output_paths",
        "audit_result",
    ],
    "properties": {
        "schema_version": {"type": "integer", "const": SKILL_RUN_SCHEMA_VERSION},
        "skill_name": {"type": "string", "minLength": 1},
        "skill_version": {"type": "string", "minLength": 1},
        "git_ref": {"type": "string", "minLength": 1},
        "created_at": {"type": "string", "minLength": 1},
        "transcript": {"type": "string"},
        "observed_actions": {"type": "array", "items": {"type": "string"}},
        "output_paths": {"type": "array", "items": {"type": "string"}, "minItems": 1},
        "audit_result": {
            "type": "object",
            "required": ["aligned", "matched_actions", "missing_actions", "mismatches"],
            "properties": {
                "aligned": {"type": "boolean"},
                "matched_actions": {"type": "array", "items": {"type": "string"}},
                "missing_actions": {"type": "array", "items": {"type": "string"}},
                "mismatches": {"type": "array", "items": {"type": "string"}},
            },
        },
        "metadata": {"type": "object", "additionalProperties": {"type": "string"}},
    },
    "additionalProperties": True,
}


def validate_skill_run_artifact(record: dict[str, Any]) -> dict[str, Any]:
    """Validate a persisted skill artifact and normalize it to a stable dictionary."""

    if not isinstance(record, dict):
        raise ValueError("skill run artifact must be a dictionary")
    if record.get("schema_version") != SKILL_RUN_SCHEMA_VERSION:
        raise ValueError(f"schema_version must be {SKILL_RUN_SCHEMA_VERSION}")

    required = [
        "skill_name",
        "skill_version",
        "git_ref",
        "created_at",
        "transcript",
        "observed_actions",
        "output_paths",
        "audit_result",
    ]
    missing = [key for key in required if key not in record]
    if missing:
        raise ValueError(f"missing required skill artifact fields: {', '.join(missing)}")

    output_paths = record.get("output_paths")
    if not isinstance(output_paths, list) or not output_paths or not all(isinstance(item, str) for item in output_paths):
        raise ValueError("output_paths must be a non-empty list of strings")

    observed_actions = record.get("observed_actions")
    if not isinstance(observed_actions, list) or not all(isinstance(item, str) for item in observed_actions):
        raise ValueError("observed_actions must be a list of strings")

    audit_result = record.get("audit_result")
    if not isinstance(audit_result, dict):
        raise ValueError("audit_result must be an object")

    for key in ("matched_actions", "missing_actions", "mismatches"):
        values = audit_result.get(key)
        if not isinstance(values, list) or not all(isinstance(item, str) for item in values):
            raise ValueError(f"audit_result.{key} must be a list of strings")

    if not isinstance(audit_result.get("aligned"), bool):
        raise ValueError("audit_result.aligned must be a boolean")

    normalized = dict(record)
    normalized["observed_actions"] = list(observed_actions)
    normalized["output_paths"] = list(output_paths)
    normalized["audit_result"] = {
        "aligned": bool(audit_result["aligned"]),
        "matched_actions": list(audit_result.get("matched_actions", [])),
        "missing_actions": list(audit_result.get("missing_actions", [])),
        "mismatches": list(audit_result.get("mismatches", [])),
    }
    normalized.setdefault("metadata", {})
    return normalized


__all__ = [
    "SKILL_RUN_SCHEMA",
    "SKILL_RUN_SCHEMA_VERSION",
    "validate_skill_run_artifact",
]
