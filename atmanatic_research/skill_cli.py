"""Command-line interface for creating, auditing, and registering skills."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .agent_skills import SkillAuditLoop, SkillManifest, SkillRegistry, SkillRunStore, build_skill_profile


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Create and register Atmanatic agent skills.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    create_parser = subparsers.add_parser("create", help="create a skill manifest")
    create_parser.add_argument("--name", required=True)
    create_parser.add_argument("--purpose", required=True)
    create_parser.add_argument("--version", required=True)
    create_parser.add_argument("--git-ref", default="main")
    create_parser.add_argument("--repository", default=None)
    create_parser.add_argument("--output-dir", action="append", default=[])
    create_parser.add_argument("--expected-action", action="append", default=[])
    create_parser.add_argument("--register-path", default="skills.json")
    create_parser.add_argument("--model-family", default="general")

    list_parser = subparsers.add_parser("list", help="list registered skill manifests")
    list_parser.add_argument("--registry-path", default="skills.json")

    status_parser = subparsers.add_parser("status", help="alias for list")
    status_parser.add_argument("--registry-path", default="skills.json")

    audit_parser = subparsers.add_parser("audit", help="audit transcript activity against a registered skill")
    audit_parser.add_argument("--skill-name", required=True)
    audit_parser.add_argument("--registry-path", default="skills.json")
    audit_parser.add_argument("--store-root", default="skill-store")
    audit_parser.add_argument("--transcript", required=True)
    audit_parser.add_argument("--observed-action", action="append", default=[])
    audit_parser.add_argument("--output-path", action="append", default=[])
    audit_parser.add_argument("--git-ref", default="main")
    audit_parser.add_argument("--json", action="store_true", help="emit structured JSON output")
    return parser


def _load_manifest(registry_path: str, skill_name: str) -> SkillManifest:
    registry = SkillRegistry(Path(registry_path))
    payload = registry.list()
    if skill_name not in payload:
        raise KeyError(f"skill {skill_name!r} was not found in the registry")
    entry = payload[skill_name]
    return SkillManifest(
        name=str(entry.get("name", skill_name)),
        purpose=str(entry.get("purpose", "")),
        version=str(entry.get("version", "0.0.0")),
        git_ref=str(entry.get("git_ref", "main")),
        repository=entry.get("repository"),
        output_directories=tuple(entry.get("output_directories", ())),
        expected_actions=tuple(entry.get("expected_actions", ())),
        model_profile=str(entry.get("model_profile", "general")),
        audit_policy=str(entry.get("audit_policy", "transcript_alignment")),
    )


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.command in {"list", "status"}:
        registry = SkillRegistry(Path(args.registry_path))
        payload = registry.list()
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 0

    if args.command == "create":
        manifest = SkillManifest(
            name=args.name,
            purpose=args.purpose,
            version=args.version,
            git_ref=args.git_ref,
            repository=args.repository,
            output_directories=tuple(args.output_dir),
            expected_actions=tuple(args.expected_action),
            model_profile=args.model_family,
        )
        registry = SkillRegistry(Path(args.register_path))
        entry = registry.register(manifest)
        profile = build_skill_profile(args.model_family)
        print(json.dumps({
            "name": manifest.name,
            "version": manifest.version,
            "instruction_style": profile.instruction_style,
            "output_directories": list(manifest.output_directories),
            "registered_at": str(args.register_path),
            "manifest": entry,
        }, indent=2, sort_keys=True))
        return 0

    if args.command == "audit":
        try:
            manifest = _load_manifest(args.registry_path, args.skill_name)
            store = SkillRunStore(Path(args.store_root))
            record = store.record_run(
                manifest,
                transcript=args.transcript,
                observed_actions=tuple(args.observed_action),
                output_paths=tuple(args.output_path),
            )
            audit = SkillAuditLoop().audit(manifest, args.transcript, observed_actions=tuple(args.observed_action))
            payload = {
                "skill_name": manifest.name,
                "version": manifest.version,
                "aligned": audit.aligned,
                "matched_actions": list(audit.matched_actions),
                "missing_actions": list(audit.missing_actions),
                "mismatches": list(audit.mismatches),
                "run_dir": str(Path(args.store_root) / "skills" / manifest.name),
                "artifact": str(record.output_paths[0]) if record.output_paths else "",
            }
            if args.json:
                print(json.dumps(payload, indent=2, sort_keys=True))
            else:
                print(json.dumps(payload, indent=2, sort_keys=True))
            return 0
        except Exception as exc:  # pragma: no cover - CLI output path
            print(json.dumps({"error": str(exc)}), file=None)
            return 1

    parser.error(f"unsupported command: {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
