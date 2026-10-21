#!/usr/bin/env python3
"""GitHub-first / bounded RDC fallback v1: source-only policy acceptance."""
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
UPSTREAM = "4e89b75d7f496dfb43fd9c1eb10a995fad53fdd8"


def route(case):
    if case["github_error"]:
        return "STOP"
    if case["github_capable"]:
        return "GITHUB"
    if case["github_ci_capable"]:
        return "GITHUB_ACTIONS"
    if case["host_only"] and case["authority"]:
        return "RDC_EXCEPTION"
    return "STOP"


class GitHubFirstRdcTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.policy = json.loads((ROOT / ".github/github-first-rdc-v1.json").read_text())
        cls.agents = (ROOT / "AGENTS.md").read_text()
        cls.docs = (ROOT / "docs/GITHUB_FIRST_RDC_ADOPTION_V1.md").read_text()
        cls.makefile = (ROOT / "Makefile").read_text()
        cls.handoff = (ROOT / "HANDOFF.md").read_text()

    def test_immutable_revision_and_consumer_identity(self):
        self.assertEqual(self.policy["schema"], "rozkalns.github-first-rdc-fallback.consumer.v1")
        self.assertEqual(self.policy["repository"], "rozkalnsandris/RPi5-maintenance")
        self.assertEqual(self.policy["upstream"]["sha"], UPSTREAM)
        self.assertIn(UPSTREAM, self.agents)
        self.assertIn(UPSTREAM, self.docs)

    def test_mandatory_github_and_hosted_ci_preference(self):
        selection = self.policy["selection"]
        self.assertTrue(selection["per_step"])
        self.assertTrue(selection["github_equivalent_mandatory"])
        self.assertTrue(selection["github_actions_when_equivalent"])
        self.assertFalse(selection["rdc_for_convenience_allowed"])
        self.assertEqual(selection["order"], [
            "GITHUB_CONNECTED_TOOLS", "GITHUB_HOSTED_CI_WHEN_APPLICABLE",
            "MINIMAL_AUTHORIZED_RDC_IF_GITHUB_INCAPABLE", "STOP"])

    def test_bounded_rdc_exception_and_fail_closed_rules(self):
        for k, v in self.policy["rdc_exception"].items():
            if k != "evidence_fields":
                self.assertTrue(v, k)
        self.assertEqual(self.policy["rdc_exception"]["evidence_fields"], [
            "STEP", "REPOSITORY_AND_TARGET", "GITHUB_CAPABILITY_CHECKED",
            "PRECISE_CAPABILITY_GAP", "GITHUB_CI_NOT_EQUIVALENT_REASON",
            "MINIMAL_RDC_OPERATION", "EXISTING_AUTHORIZATION",
            "GITHUB_RETURN_EVIDENCE"])
        for k, v in self.policy["fail_closed"].items():
            self.assertTrue(v, k)

    def test_decision_matrix(self):
        cases = self.policy["decision_cases"]
        self.assertEqual(len(cases), 8)
        self.assertEqual(len({c["scenario"] for c in cases}), len(cases))
        for case in cases:
            with self.subTest(case=case["scenario"]):
                self.assertEqual(route(case), case["expected"])

    def test_local_maintenance_and_handoff_boundaries(self):
        for k, v in self.policy["local_boundaries"].items():
            self.assertTrue(v, k)
        for required in (
            "MERGE always requires separate explicit owner authorization.",
            "Merge authorization is never production authorization.",
            "A one-time LIVE authorization is consumed",
            "A previously reviewed and explicitly installed scheduled maintenance",
            "No repository workflow, agent or doctor may autonomously mutate",
            "If mutation has started and any tool error",
        ):
            self.assertIn(required, self.agents)
        self.assertIn("Current handoff", self.handoff)
        self.assertIn("issue #23", self.handoff.lower())

    def test_ci_wiring_and_no_new_execution_authority(self):
        self.assertIn("python3 ./tests/test-github-first-rdc-v1.py", self.makefile)
        self.assertIn("validate: bootstrap-check static test", self.makefile)
        self.assertIn("No new GITHUB-ONLY mode", self.docs)
        self.assertIn("no `ops/**`", self.docs)
        self.assertNotIn("wrangler deploy", self.docs)
        self.assertNotIn("systemctl restart", self.docs)


if __name__ == "__main__":
    unittest.main()
