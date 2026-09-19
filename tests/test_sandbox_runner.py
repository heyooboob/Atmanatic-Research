import os
import sys
import unittest

from atmanatic_research import (
    SandboxError,
    SandboxLimits,
    run_sandboxed,
    run_verification_in_sandbox,
)

PYTHON = sys.executable


class SandboxLimitsTests(unittest.TestCase):
    def test_rejects_non_positive_wall_clock(self):
        with self.assertRaises(SandboxError):
            SandboxLimits(wall_clock_seconds=0)

    def test_rejects_non_positive_cpu_seconds(self):
        with self.assertRaises(SandboxError):
            SandboxLimits(wall_clock_seconds=1, cpu_seconds=0)

    def test_rejects_non_positive_memory_bytes(self):
        with self.assertRaises(SandboxError):
            SandboxLimits(wall_clock_seconds=1, memory_bytes=0)


class RunSandboxedTests(unittest.TestCase):
    def test_rejects_empty_argv(self):
        with self.assertRaises(SandboxError):
            run_sandboxed([], limits=SandboxLimits(wall_clock_seconds=1))

    def test_completed_process_is_reported(self):
        result = run_sandboxed(
            [PYTHON, "-c", "print('hello')"], limits=SandboxLimits(wall_clock_seconds=5)
        )
        self.assertEqual(result.status, "completed")
        self.assertEqual(result.exit_code, 0)
        self.assertEqual(result.stdout.strip(), b"hello")
        self.assertTrue(result.limits_enforced["wall_clock"])
        self.assertFalse(result.limits_enforced["network_denied"])

    def test_wall_clock_timeout_is_enforced(self):
        result = run_sandboxed(
            [PYTHON, "-c", "import time; time.sleep(5)"],
            limits=SandboxLimits(wall_clock_seconds=0.2),
        )
        self.assertEqual(result.status, "timed_out")
        self.assertIsNone(result.exit_code)

    def test_network_environment_variables_are_stripped(self):
        os.environ["HTTP_PROXY"] = "http://example.invalid:8080"
        try:
            result = run_sandboxed(
                [PYTHON, "-c", "import os; print(os.environ.get('HTTP_PROXY', 'unset'))"],
                limits=SandboxLimits(wall_clock_seconds=5),
            )
        finally:
            del os.environ["HTTP_PROXY"]
        self.assertEqual(result.stdout.strip(), b"unset")

    @unittest.skipUnless(os.name == "posix", "resource limits are only enforced on POSIX")
    def test_cpu_limit_is_enforced_on_posix(self):
        result = run_sandboxed(
            [PYTHON, "-c", "x = 0\nwhile True:\n    x += 1"],
            limits=SandboxLimits(wall_clock_seconds=5, cpu_seconds=1),
        )
        self.assertTrue(result.limits_enforced["cpu"])
        self.assertEqual(result.status, "completed")
        self.assertNotEqual(result.exit_code, 0)


class RunVerificationInSandboxTests(unittest.TestCase):
    def _run(self, code: str, **overrides):
        defaults = dict(
            argv=[PYTHON, "-c", code],
            verifier_name="fixture-sandbox-verifier",
            verifier_version="1.0.0",
            input_artifact_hash="a" * 64,
            specification_ids=["spec:fixture"],
            environment_id="test",
            limits=SandboxLimits(wall_clock_seconds=5),
        )
        defaults.update(overrides)
        return run_verification_in_sandbox(**defaults)

    def test_well_formed_success_is_verified(self):
        record = self._run("import json; print(json.dumps({'ok': True, 'diagnostics': []}))")
        self.assertEqual(record["status"], "verified")
        self.assertEqual(record["diagnostics"], [])
        self.assertFalse(record["execution_authorized"])

    def test_well_formed_failure_is_failed_not_verified(self):
        record = self._run(
            "import json; print(json.dumps({'ok': False, 'diagnostics': ['invariant violated']}))"
        )
        self.assertEqual(record["status"], "failed")
        self.assertIn("invariant violated", record["diagnostics"])

    def test_malformed_stdout_is_rejected_as_failed(self):
        record = self._run("print('not json')")
        self.assertEqual(record["status"], "failed")
        self.assertTrue(any("stdout" in d for d in record["diagnostics"]))

    def test_nonzero_exit_is_rejected_as_failed(self):
        record = self._run(
            "import json, sys; print(json.dumps({'ok': True, 'diagnostics': []})); sys.exit(1)"
        )
        self.assertEqual(record["status"], "failed")

    def test_timeout_is_recorded_as_timed_out(self):
        record = self._run(
            "import time; time.sleep(5)", limits=SandboxLimits(wall_clock_seconds=0.2)
        )
        self.assertEqual(record["status"], "timed_out")

    def test_result_is_a_valid_verification_result(self):
        record = self._run("import json; print(json.dumps({'ok': True, 'diagnostics': []}))")
        # Constructing the record already runs it through validate_verification_result;
        # a second call proves the returned object is stable and re-validates cleanly.
        from atmanatic_research import validate_verification_result

        validate_verification_result(record)


if __name__ == "__main__":
    unittest.main()
