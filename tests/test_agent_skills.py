import json
import os
import tempfile
import unittest

from atmanatic_research import (
    SkillAuditLoop,
    SkillAuditResult,
    SkillManifest,
    SkillRegistry,
    SkillRunRecord,
    SkillRunStore,
    audit_skill_transcript,
    build_skill_creator_template,
    build_skill_profile,
)
from atmanatic_research.skill_cli import main as skill_cli_main


class AgentSkillLifecycleTests(unittest.TestCase):
    def test_skill_manifest_requires_versioning_and_output_tracking(self):
        with self.assertRaises(ValueError):
            SkillManifest(
                name="research-skill",
                purpose="review evidence",
                output_directories=(),
                expected_actions=("inspect evidence",),
                version="",
            )

    def test_transcript_audit_detects_misalignment(self):
        manifest = SkillManifest(
            name="research-skill",
            purpose="review evidence",
            version="1.0.0",
            git_ref="main",
            repository="https://github.com/example/repo",
            output_directories=("runs/", "logs/"),
            expected_actions=("inspect evidence", "record finding"),
            model_profile="legacy",
        )

        transcript = "The agent summarized the claim and skipped the review, without recording anything."
        result = audit_skill_transcript(manifest, transcript)

        self.assertIsInstance(result, SkillAuditResult)
        self.assertFalse(result.aligned)
        self.assertIn("inspect evidence", result.missing_actions)
        self.assertIn("record finding", result.missing_actions)

    def test_legacy_models_get_prescriptive_instructions(self):
        profile = build_skill_profile("gpt-4o-mini")
        self.assertEqual(profile.instruction_style, "prescriptive")
        self.assertTrue(profile.context_is_explicit)

        modern = build_skill_profile("claude-3.5-sonnet")
        self.assertEqual(modern.instruction_style, "goal-oriented")
        self.assertFalse(modern.context_is_explicit)

    def test_skill_template_tracks_runs_and_audit_plan(self):
        template = build_skill_creator_template(
            name="evidence-auditor",
            purpose="Validate evidence before a claim is accepted.",
            model_family="claude-3.5-sonnet",
            output_directories=("runs/", "logs/"),
        )

        self.assertEqual(template.name, "evidence-auditor")
        self.assertIn("runs/", template.output_directories)
        self.assertEqual(template.audit_policy, "transcript_alignment")
        self.assertEqual(template.model_profile.instruction_style, "goal-oriented")

    def test_run_record_keeps_versions_and_outputs(self):
        record = SkillRunRecord(
            skill_name="research-skill",
            skill_version="1.0.0",
            git_ref="main",
            transcript="inspected evidence and recorded finding",
            output_paths=("runs/research-1.json",),
            audit_result=SkillAuditResult(aligned=True, matched_actions=("inspected evidence",), missing_actions=(), mismatches=()),
        )

        self.assertEqual(record.skill_version, "1.0.0")
        self.assertEqual(record.output_paths, ("runs/research-1.json",))
        self.assertTrue(record.audit_result.aligned)

    def test_persistent_run_store_records_skill_runs(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            store = SkillRunStore(tmpdir)
            manifest = SkillManifest(
                name="evidence-auditor",
                purpose="validate evidence before claims are accepted",
                version="0.2.0",
                git_ref="feature/skill-store",
                repository="https://github.com/example/skills",
                output_directories=("runs/", "logs/"),
                expected_actions=("inspect evidence", "document finding"),
                model_profile="claude-3.5-sonnet",
            )
            record = store.record_run(
                manifest,
                transcript="I inspected the evidence and documented the finding.",
                observed_actions=("inspect evidence", "document finding"),
                output_paths=("runs/evidence-auditor-1.json", "logs/evidence-auditor-1.log"),
            )

            self.assertEqual(record.skill_version, "0.2.0")
            self.assertTrue(os.path.exists(record.output_paths[0]))
            self.assertTrue(os.path.exists(record.output_paths[1]))
            self.assertEqual(store.latest_run("evidence-auditor").skill_version, "0.2.0")

    def test_audit_loop_compares_expected_and_observed_actions(self):
        manifest = SkillManifest(
            name="research-skill",
            purpose="review evidence",
            version="1.0.0",
            git_ref="main",
            repository="https://github.com/example/repo",
            output_directories=("runs/", "logs/"),
            expected_actions=("inspect evidence", "record finding"),
            model_profile="gpt-4o-mini",
        )
        transcript = "The agent inspected evidence and recorded the finding for the reviewer."

        audit = SkillAuditLoop().audit(manifest, transcript, observed_actions=("inspect evidence", "record finding"))

        self.assertTrue(audit.aligned)
        self.assertEqual(audit.missing_actions, ())

    def test_skill_registry_cli_creates_and_registers_manifest(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            registry_path = os.path.join(tmpdir, "skills.json")
            status = skill_cli_main([
                "create",
                "--name",
                "quality-review",
                "--purpose",
                "Validate output quality before release.",
                "--version",
                "0.1.0",
                "--output-dir",
                "runs",
                "--output-dir",
                "logs",
                "--register-path",
                registry_path,
                "--model-family",
                "gpt-4o-mini",
            ])

            self.assertEqual(status, 0)
            with open(registry_path, "r", encoding="utf-8") as handle:
                payload = json.load(handle)
            self.assertIn("quality-review", payload)
            self.assertEqual(payload["quality-review"]["version"], "0.1.0")

    def test_skill_audit_cli_returns_audit_status_and_persists_run(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            registry_path = os.path.join(tmpdir, "skills.json")
            store_root = os.path.join(tmpdir, "skill-store")
            skill_cli_main([
                "create",
                "--name",
                "quality-review",
                "--purpose",
                "Validate output quality before release.",
                "--version",
                "0.2.0",
                "--output-dir",
                "runs",
                "--output-dir",
                "logs",
                "--register-path",
                registry_path,
                "--expected-action",
                "inspect evidence",
                "--expected-action",
                "record finding",
                "--model-family",
                "gpt-4o-mini",
            ])
            status = skill_cli_main([
                "audit",
                "--skill-name",
                "quality-review",
                "--registry-path",
                registry_path,
                "--store-root",
                store_root,
                "--transcript",
                "The agent inspected evidence and recorded the finding.",
                "--observed-action",
                "inspect evidence",
                "--observed-action",
                "record finding",
            ])
            self.assertEqual(status, 0)
            self.assertTrue(os.path.exists(os.path.join(store_root, "skills", "quality-review")))
            self.assertTrue(os.path.exists(os.path.join(store_root, "skill_runs.json")))

    def test_skill_run_store_uses_timestamped_run_folders(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            store = SkillRunStore(tmpdir)
            manifest = SkillManifest(
                name="evidence-auditor",
                purpose="validate evidence before claims are accepted",
                version="0.2.1",
                output_directories=("runs/", "logs/"),
                expected_actions=("inspect evidence", "document finding"),
                model_profile="claude-3.5-sonnet",
            )
            record = store.record_run(
                manifest,
                transcript="I inspected the evidence and documented the finding.",
                observed_actions=("inspect evidence", "document finding"),
                output_paths=("runs/evidence-auditor.json", "logs/evidence-auditor.log"),
            )

            run_dir = os.path.dirname(record.output_paths[0])
            self.assertIn("skills", run_dir)
            self.assertTrue(os.path.exists(os.path.join(os.path.dirname(run_dir), "artifact.json")))
