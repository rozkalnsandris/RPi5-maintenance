#!/usr/bin/env python3
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / ".github" / "github-api-access-v1.json"
AGENTS = ROOT / "AGENTS.md"


def test_manifest_contract() -> None:
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))

    assert data["schema"] == "rozkalns.github-api-access-consumer.v1"
    assert data["repository"] == "rozkalnsandris/RPi5-maintenance"
    assert data["canonical_contract"]["shared_revision"] == (
        "3bb0740b5f0a8ce631d2ff79f1acc4999ff6ed2c"
    )

    read_plan = data["read_plan"]
    assert read_plan["serial"] is True
    assert read_plan["minimum_sufficient"] is True
    assert read_plan["changed_files_on_demand"] is True
    assert read_plan["tight_polling"] is False

    expected_dispositions = {
        "PRIMARY_RATE_LIMIT_EXHAUSTED",
        "SECONDARY_RATE_LIMIT_SUSPECTED",
        "RETRY_AFTER_REQUIRED",
        "RESET_WAIT_REQUIRED",
        "READ_BACKOFF_REQUIRED",
        "TRANSPORT_RATE_LIMIT_METADATA_UNAVAILABLE",
    }
    assert set(read_plan["stable_dispositions"]) == expected_dispositions

    mutation = data["mutation_boundary"]
    assert mutation["expected_head_required"] is True
    assert mutation["authorization_consumed_on_dispatch"] is True
    assert mutation["duplicate_mutation_after_403_429_timeout_transport"] is False
    assert mutation["ambiguous_outcome_action"] == "READ_ONLY_RECONCILE_THEN_STOP"
    assert mutation["merge_implies_live"] is False

    assert set(data["synthetic_ambiguity_coverage"]) == {
        "post-dispatch-429",
        "post-dispatch-timeout",
        "post-dispatch-transport",
    }


def test_local_authority_stays_stricter() -> None:
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    rules = data["local_stricter_rules"]
    agents = AGENTS.read_text(encoding="utf-8")

    assert rules["explicit_merge_authorization"] is True
    assert rules["separate_live_authorization"] is True
    assert rules["fail_closed_after_mutation_ambiguity"] is True
    assert rules["three_failed_attempts_stop"] is True

    assert "MERGE always requires separate explicit owner authorization." in agents
    assert "Merge authorization is never production authorization." in agents
    assert "No repository workflow, agent or doctor may autonomously mutate the production RPi5." in agents
    assert "Do not automatically retry, rollback, clean up, reboot or choose an alternate mutation path" in agents


if __name__ == "__main__":
    test_manifest_contract()
    test_local_authority_stays_stricter()
