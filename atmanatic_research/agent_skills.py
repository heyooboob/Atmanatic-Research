"""Operational guidance for versioned, auditable agent skills.

The project treats agent skills as software artifacts rather than ad hoc prompt
strings. A skill should be versioned, produce traceable outputs, and be evaluated
against the actual transcript of the invoking agent.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Sequence


@dataclass(frozen=True)
class SkillProfile:
    """Model-specific guidance profile for a skill."""

    model_family: str
    instruction_style: str
    context_is_explicit: bool
    notes: tuple[str, ...] = ()


@dataclass(frozen=True)
class SkillManifest:
    """Versioned metadata for a reusable agent skill."""

    name: str
    purpose: str
    version: str
    git_ref: str = "main"
    repository: str | None = None
    output_directories: tuple[str, ...] = ()
    expected_actions: tuple[str, ...] = ()
    model_profile: str = "general"
    audit_policy: str = "transcript_alignment"

    def __post_init__(self) -> None:
        if not self.name or not self.name.strip():
            raise ValueError("name must be a non-empty string")
        if not self.version or not self.version.strip():
            raise ValueError("version must be a non-empty string")
        if not self.purpose or not self.purpose.strip():
            raise ValueError("purpose must be a non-empty string")
        if not self.output_directories:
            raise ValueError("output_directories must contain at least one folder")
        normalized = tuple(item.strip() for item in self.output_directories if item and item.strip())
        if not normalized:
            raise ValueError("output_directories must contain at least one non-empty folder")
        object.__setattr__(self, "output_directories", normalized)
        object.__setattr__(self, "expected_actions", tuple(action.strip() for action in self.expected_actions if action and action.strip()))


@dataclass(frozen=True)
class SkillAuditResult:
    """Result of auditing an agent transcript against a skill's intended behavior."""

    aligned: bool
    matched_actions: tuple[str, ...] = ()
    missing_actions: tuple[str, ...] = ()
    mismatches: tuple[str, ...] = ()
    events: tuple[dict[str, str], ...] = ()
    summary: dict[str, int] = field(default_factory=dict)


@dataclass(frozen=True)
class SkillRunRecord:
    """A run snapshot capturing a skill version, transcript, and output paths."""

    skill_name: str
    skill_version: str
    git_ref: str
    transcript: str
    output_paths: tuple[str, ...]
    audit_result: SkillAuditResult
    metadata: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class SkillCreatorTemplate:
    """Structured template for building a new skill with disciplined controls."""

    name: str
    purpose: str
    model_family: str
    output_directories: tuple[str, ...]
    audit_policy: str
    model_profile: SkillProfile


class SkillRegistry:
    """Persistent manifest registry for versioned skills."""

    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if self.path.exists() and self.path.is_dir():
            raise ValueError("registry path must be a file path, not a directory")

    def _load(self) -> dict[str, dict[str, object]]:
        if not self.path.exists():
            return {}
        with self.path.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
        if not isinstance(data, dict):
            raise ValueError("registry payload must be a dictionary")
        return data

    def register(self, manifest: SkillManifest) -> dict[str, object]:
        payload = self._load()
        entry = {
            "name": manifest.name,
            "purpose": manifest.purpose,
            "version": manifest.version,
            "git_ref": manifest.git_ref,
            "repository": manifest.repository,
            "output_directories": list(manifest.output_directories),
            "expected_actions": list(manifest.expected_actions),
            "model_profile": manifest.model_profile,
            "audit_policy": manifest.audit_policy,
        }
        payload[manifest.name] = entry
        with self.path.open("w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2, sort_keys=True)
        return entry

    def list(self) -> dict[str, dict[str, object]]:
        return self._load()


class SkillRunStore:
    """Persist consumer-local run metadata and generated outputs.

    The store records observations for local skill evaluation. It does not
    publish telemetry, change a skill version, or promote a behavior into the
    public package; those decisions require a reviewed release change.
    """

    def __init__(self, root_dir: str | Path):
        self.root_dir = Path(root_dir)
        self.root_dir.mkdir(parents=True, exist_ok=True)
        self.skills_dir = self.root_dir / "skills"
        self.skills_dir.mkdir(parents=True, exist_ok=True)
        (self.root_dir / "logs").mkdir(parents=True, exist_ok=True)
        self.index_path = self.root_dir / "skill_runs.json"

    def _timestamp(self) -> str:
        return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")

    def _normalize_output_path(self, value: str, *, run_dir: Path) -> str:
        candidate = Path(value)
        if candidate.is_absolute():
            target = candidate
        else:
            relative = candidate.as_posix().lstrip("/")
            target = run_dir / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.touch(exist_ok=True)
        return str(target)

    def _run_dir_for(self, manifest: SkillManifest) -> Path:
        timestamp = self._timestamp()
        run_dir = self.skills_dir / manifest.name / timestamp
        run_dir.mkdir(parents=True, exist_ok=True)
        return run_dir

    def _write_artifact_file(self, run_dir: Path, manifest: SkillManifest, record: SkillRunRecord) -> None:
        artifact = {
            "schema_version": 1,
            "skill_name": record.skill_name,
            "skill_version": record.skill_version,
            "git_ref": record.git_ref,
            "created_at": self._timestamp(),
            "transcript": record.transcript,
            "observed_actions": json.loads(record.metadata.get("observed_actions", "[]")) if record.metadata.get("observed_actions") else [],
            "output_paths": list(record.output_paths),
            "audit_result": {
                "aligned": record.audit_result.aligned,
                "matched_actions": list(record.audit_result.matched_actions),
                "missing_actions": list(record.audit_result.missing_actions),
                "mismatches": list(record.audit_result.mismatches),
                "events": [dict(event) for event in record.audit_result.events],
                "summary": dict(record.audit_result.summary),
            },
            "metadata": {
                "repository": manifest.repository or "",
                "model_profile": manifest.model_profile,
                "purpose": manifest.purpose,
                "output_directories": list(manifest.output_directories),
                "audit_policy": manifest.audit_policy,
                "run_id": run_dir.name,
            },
        }
        artifact_path = run_dir / "artifact.json"
        with artifact_path.open("w", encoding="utf-8") as handle:
            json.dump(artifact, handle, indent=2, sort_keys=True)

    def _load_index(self) -> dict[str, Any]:
        if not self.index_path.exists():
            return {"skills": {}}
        with self.index_path.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
        if not isinstance(data, dict):
            return {"skills": {}}
        if "skills" not in data:
            data["skills"] = {}
        return data

    def _write_index(self, payload: dict[str, Any]) -> None:
        with self.index_path.open("w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2, sort_keys=True)

    def record_run(
        self,
        manifest: SkillManifest,
        *,
        transcript: str,
        observed_actions: Sequence[str] | None = None,
        output_paths: Sequence[str] | None = None,
    ) -> SkillRunRecord:
        if not isinstance(manifest, SkillManifest):
            raise TypeError("manifest must be a SkillManifest")

        run_dir = self._run_dir_for(manifest)
        normalized_outputs = tuple(
            self._normalize_output_path(path, run_dir=run_dir)
            for path in (output_paths or ())
        )
        if not normalized_outputs:
            default_path = run_dir / "outputs" / f"{manifest.name}.json"
            default_path.parent.mkdir(parents=True, exist_ok=True)
            default_path.touch(exist_ok=True)
            normalized_outputs = (str(default_path),)

        audit = SkillAuditLoop().audit(manifest, transcript, observed_actions=observed_actions)
        record = SkillRunRecord(
            skill_name=manifest.name,
            skill_version=manifest.version,
            git_ref=manifest.git_ref,
            transcript=transcript,
            output_paths=normalized_outputs,
            audit_result=audit,
            metadata={
                "repository": manifest.repository or "",
                "model_profile": manifest.model_profile,
                "observed_actions": json.dumps(list(observed_actions or ())),
            },
        )

        self._write_artifact_file(run_dir, manifest, record)

        payload = self._load_index()
        entry = {
            "skill_version": record.skill_version,
            "git_ref": record.git_ref,
            "transcript": record.transcript,
            "output_paths": list(record.output_paths),
            "audit_result": {
                "aligned": record.audit_result.aligned,
                "matched_actions": list(record.audit_result.matched_actions),
                "missing_actions": list(record.audit_result.missing_actions),
                "mismatches": list(record.audit_result.mismatches),
                "events": [dict(event) for event in record.audit_result.events],
                "summary": dict(record.audit_result.summary),
            },
            "run_dir": str(run_dir),
            "created_at": self._timestamp(),
        }
        payload.setdefault(manifest.name, [])
        payload[manifest.name].append(entry)
        payload.setdefault("skills", {})
        payload["skills"].setdefault(manifest.name, [])
        payload["skills"][manifest.name].append(entry)
        self._write_index(payload)
        return record

    def latest_run(self, skill_name: str) -> SkillRunRecord | None:
        payload = self._load_index()
        runs = payload.get(skill_name, [])
        if not runs:
            return None
        latest = runs[-1]
        audit_payload = latest.get("audit_result", {})
        return SkillRunRecord(
            skill_name=skill_name,
            skill_version=str(latest.get("skill_version", "unknown")),
            git_ref=str(latest.get("git_ref", "main")),
            transcript=str(latest.get("transcript", "")),
            output_paths=tuple(latest.get("output_paths", ())),
            audit_result=SkillAuditResult(
                aligned=bool(audit_payload.get("aligned", False)),
                matched_actions=tuple(audit_payload.get("matched_actions", ())),
                missing_actions=tuple(audit_payload.get("missing_actions", ())),
                mismatches=tuple(audit_payload.get("mismatches", ())),
                events=tuple(dict(event) for event in audit_payload.get("events", ())),
                summary=dict(audit_payload.get("summary", {})),
            ),
            metadata={"repository": "", "run_dir": str(latest.get("run_dir", ""))},
        )


class SkillAuditLoop:
    """Compare intended actions to actual agent behavior stored in transcripts and observations."""

    def audit(
        self,
        manifest: SkillManifest,
        transcript: str,
        *,
        observed_actions: Sequence[str] | None = None,
    ) -> SkillAuditResult:
        if not isinstance(manifest, SkillManifest):
            raise TypeError("manifest must be a SkillManifest")
        transcript_text = (transcript or "").lower()
        observed = tuple(
            str(item).strip().lower()
            for item in (observed_actions or ())
            if isinstance(item, str) and str(item).strip()
        )

        matched: list[str] = []
        missing: list[str] = []
        mismatches: list[str] = []
        events: list[dict[str, str]] = []

        for action in manifest.expected_actions:
            normalized_action = action.lower()
            present_in_transcript = normalized_action in transcript_text
            present_in_observed = any(
                normalized_action == item or normalized_action in item
                for item in observed
            )
            if present_in_transcript or present_in_observed:
                matched.append(action)
                source = "transcript"
                if present_in_observed and not present_in_transcript:
                    source = "observed_actions"
                elif present_in_transcript and present_in_observed:
                    source = "transcript+observed_actions"
                events.append({"action": action, "status": "matched", "source": source})
            else:
                missing.append(action)
                events.append({"action": action, "status": "missing", "source": "none"})

        if observed and not matched:
            mismatches.append("observed actions failed to account for expected actions")
        if not missing and not matched and manifest.expected_actions:
            mismatches.append("there were no actionable matches")

        summary = {
            "total_expected": len(manifest.expected_actions),
            "total_matched": len(matched),
            "total_missing": len(missing),
            "total_mismatches": len(mismatches),
        }

        return SkillAuditResult(
            aligned=not missing,
            matched_actions=tuple(matched),
            missing_actions=tuple(missing),
            mismatches=tuple(mismatches),
            events=tuple(events),
            summary=summary,
        )


def build_skill_profile(model_family: str) -> SkillProfile:
    """Map a model family to the instruction style expected by the skill.

    Older and smaller models do best with a more prescriptive, explicit style.
    Newer models respond better to goal-oriented instructions with less
    hand-holding.
    """

    family = (model_family or "").lower()
    if any(marker in family for marker in ("mini", "legacy", "small", "gpt-4o-mini", "gpt-3.5", "claude-2")):
        return SkillProfile(
            model_family=model_family,
            instruction_style="prescriptive",
            context_is_explicit=True,
            notes=("Provide explicit decision steps, guardrails, and required output structure.",),
        )

    return SkillProfile(
        model_family=model_family,
        instruction_style="goal-oriented",
        context_is_explicit=False,
        notes=("State the objective clearly and allow the model to choose the execution path.",),
    )


def audit_skill_transcript(manifest: SkillManifest, transcript: str) -> SkillAuditResult:
    """Check whether an agent transcript actually aligned with skill intent."""
    return SkillAuditLoop().audit(manifest, transcript)


def build_skill_creator_template(
    *,
    name: str,
    purpose: str,
    model_family: str,
    output_directories: Iterable[str],
) -> SkillCreatorTemplate:
    """Create a disciplined skill design template that enforces versioning and auditability."""

    normalized_dirs = tuple(str(item).strip() for item in output_directories if item and str(item).strip())
    if not normalized_dirs:
        raise ValueError("output_directories must contain at least one folder")

    profile = build_skill_profile(model_family)
    return SkillCreatorTemplate(
        name=name,
        purpose=purpose,
        model_family=model_family,
        output_directories=normalized_dirs,
        audit_policy="transcript_alignment",
        model_profile=profile,
    )


__all__ = [
    "SkillAuditLoop",
    "SkillAuditResult",
    "SkillCreatorTemplate",
    "SkillManifest",
    "SkillProfile",
    "SkillRegistry",
    "SkillRunRecord",
    "SkillRunStore",
    "audit_skill_transcript",
    "build_skill_creator_template",
    "build_skill_profile",
]
