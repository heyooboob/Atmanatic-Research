import unittest

from validity_protocol.levels import ValidityLevel

from atmanatic_research import (
    check_validity_transition_table,
    run_validity_transition_pilot,
    validate_verification_result,
)


class CheckValidityTransitionTableTests(unittest.TestCase):
    def test_real_ladder_has_no_diagnostics(self):
        ok, diagnostics = check_validity_transition_table()
        self.assertTrue(ok)
        self.assertEqual(diagnostics, [])

    def test_broken_reachability_is_flagged(self):
        ok, diagnostics = check_validity_transition_table(can_advance_fn=lambda source, target: False)
        self.assertFalse(ok)
        self.assertTrue(any("not reachable" in d for d in diagnostics))

    def test_broken_monotonicity_is_flagged(self):
        ok, diagnostics = check_validity_transition_table(can_advance_fn=lambda source, target: True)
        self.assertFalse(ok)
        self.assertTrue(any("non-forward level" in d for d in diagnostics))


class RunValidityTransitionPilotTests(unittest.TestCase):
    def test_pilot_verifies_the_real_ladder(self):
        record = run_validity_transition_pilot(environment_id="ci-python-312")
        self.assertEqual(record["status"], "verified")
        self.assertEqual(record["diagnostics"], [])
        validate_verification_result(record)

    def test_pilot_is_reproducible_in_verdict_and_diagnostics(self):
        first = run_validity_transition_pilot(environment_id="ci-python-312")
        second = run_validity_transition_pilot(environment_id="ci-python-312")
        self.assertEqual(first["status"], second["status"])
        self.assertEqual(first["diagnostics"], second["diagnostics"])
        self.assertEqual(first["input_artifact_hash"], second["input_artifact_hash"])

    def test_pilot_result_never_authorizes_execution(self):
        record = run_validity_transition_pilot(environment_id="ci-python-312")
        self.assertFalse(record["execution_authorized"])

    def test_two_runs_never_share_an_artifact_id(self):
        first = run_validity_transition_pilot(environment_id="ci-python-312")
        second = run_validity_transition_pilot(environment_id="ci-python-312")
        self.assertNotEqual(first["artifact_id"], second["artifact_id"])

    def test_caller_supplied_artifact_id_is_honored(self):
        record = run_validity_transition_pilot(environment_id="ci-python-312", artifact_id="run-42")
        self.assertEqual(record["artifact_id"], "run-42")


if __name__ == "__main__":
    unittest.main()
