#!/usr/bin/env python3
from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
ADAPTER = ROOT / "ops/lib/rpi5-docker-retention-inventory.py"
PLANNER = ROOT / "ops/lib/rpi5-docker-retention-plan.py"
FIXTURE = ROOT / "tests/fixtures/docker-retention/runtime-inventory.json"


def load_adapter():
    spec = importlib.util.spec_from_file_location("inventory", ADAPTER)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def fixture() -> dict:
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def run_planner(payload: dict) -> dict:
    proc = subprocess.run(["python3", str(PLANNER)], input=json.dumps(payload), text=True, capture_output=True, check=False)
    assert proc.returncode == 0, proc.stderr
    return json.loads(proc.stdout)


def test_adapter_builds_protected_roles() -> None:
    module = load_adapter()
    result = module.build_inventory(fixture())
    service = result["services"][0]
    assert service["current_id"].endswith("a" * 64)
    assert service["candidate_ids"] == ["sha256:" + "b" * 64]
    assert service["previous_known_good_ids"] == ["sha256:" + "c" * 64]
    images = {item["id"]: item for item in result["images"]}
    assert images["sha256:" + "a" * 64]["container_refs"] == ["project_app_1"]
    assert images["sha256:" + "e" * 64]["container_refs"] == ["other_app_1"]


def test_end_to_end_planner_only_selects_superseded_managed_image() -> None:
    module = load_adapter()
    plan = run_planner(module.build_inventory(fixture()))
    assert plan["delete_ids"] == ["sha256:" + "d" * 64]
    assert plan["build_cache"]["action"] == "report-only"
    assert all(item["action"] == "report-only" for item in plan["volumes"])


def test_untrusted_rollback_evidence_is_not_accepted() -> None:
    module = load_adapter()
    payload = fixture()
    payload["rollback_evidence"][0]["source"] = "manual-note"
    adapted = module.build_inventory(payload)
    assert adapted["services"][0]["previous_known_good_ids"] == []
    plan = run_planner(adapted)
    assert plan["delete_ids"] == []
    assert plan["blocked_lineages"] == {"repo/app": ["missing-previous-known-good"]}


def test_global_container_reference_protects_unmanaged_image() -> None:
    module = load_adapter()
    plan = run_planner(module.build_inventory(fixture()))
    unmanaged = next(item for item in plan["images"] if item["id"] == "sha256:" + "e" * 64)
    assert unmanaged["action"] == "protect"
    assert unmanaged["role"] == "container-referenced"


def test_candidate_outside_lineage_fails_closed() -> None:
    module = load_adapter()
    payload = fixture()
    payload["managed_services"][0]["candidate_ids"] = ["sha256:" + "e" * 64]
    try:
        module.build_inventory(payload)
    except ValueError as exc:
        assert "candidate image outside lineage" in str(exc)
    else:
        raise AssertionError("expected fail-closed candidate-lineage rejection")


def test_adapter_has_no_runtime_or_mutation_commands() -> None:
    text = ADAPTER.read_text(encoding="utf-8")
    for forbidden in ("subprocess", "docker ", "systemctl", "image rm", "prune", "unlink(", "remove("):
        assert forbidden not in text


if __name__ == "__main__":
    test_adapter_builds_protected_roles()
    test_end_to_end_planner_only_selects_superseded_managed_image()
    test_untrusted_rollback_evidence_is_not_accepted()
    test_global_container_reference_protects_unmanaged_image()
    test_candidate_outside_lineage_fails_closed()
    test_adapter_has_no_runtime_or_mutation_commands()
    print("Docker retention inventory adapter tests: PASS")
