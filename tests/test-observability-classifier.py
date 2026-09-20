#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
CLASSIFIER = ROOT / "ops/lib/rpi5-observability-classifier.py"
FIXTURES = ROOT / "tests/fixtures/observability"


def run_fixture(name: str, *, expect_ok: bool = True) -> dict | None:
    proc = subprocess.run(
        ["python3", str(CLASSIFIER), str(FIXTURES / name)],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if expect_ok:
        assert proc.returncode == 0, proc.stderr
        return json.loads(proc.stdout)
    assert proc.returncode == 2
    return None


def by_key(result: dict, key: str) -> dict:
    return next(item for item in result["services"] if item["key"] == key)


def test_rdc_pending_auth_overrides_active() -> None:
    result = run_fixture("rdc-pending-auth.json")
    assert result is not None
    rdc = by_key(result, "user:remote-desktop-commander.service")
    assert rdc["active_state"] == "active"
    assert rdc["state"] == "authorization-required"
    assert rdc["root_causes"] == ["service.authorization-required"]
    assert rdc["authorization_evidence"]


def test_recovered_loop_oom_and_hermes_are_distinct() -> None:
    result = run_fixture("mixed-recovered-oom-hermes.json")
    assert result is not None

    rdc = by_key(result, "user:remote-desktop-commander.service")
    loop = by_key(result, "system:example-loop.service")
    assert rdc["state"] == "recovered-transient"
    assert rdc["recovered"] is True
    assert loop["state"] == "failure-loop"

    memory_classes = [item["class"] for item in result["memory"]]
    assert memory_classes == [
        "kernel-oom",
        "cgroup-oom",
        "user-space-v8-oom",
        "user-space-runtime-oom",
    ]

    hermes_classes = [item["class"] for item in result["hermes"]["findings"]]
    assert "execution-failure" in hermes_classes
    assert "delivery-failure" in hermes_classes
    assert "unknown-attempt" in hermes_classes
    assert "catch-up-dispatch" in hermes_classes
    assert "doctor-failure" in hermes_classes
    assert "parked-next-run" in hermes_classes
    assert "hermes.execution-failure" in result["root_causes"]
    assert "hermes.delivery-failure" in result["root_causes"]


def test_fail_closed_stale_and_not_ready_are_separate() -> None:
    result = run_fixture("failclosed-stale-notready.json")
    assert result is not None
    assert by_key(result, "system:guard.service")["state"] == "intentional-fail-closed"
    assert by_key(result, "system:stale.service")["state"] == "historical-stale-failure"
    assert by_key(result, "system:authless.service")["state"] == "active-not-ready"


def test_invalid_input_fails_closed() -> None:
    payload = {
        "schema": "rpi5-observability-evidence.v1",
        "now_epoch": 2_000_000,
        "services": [{"manager": "user", "unit": "x.service"}],
    }
    proc = subprocess.run(
        ["python3", str(CLASSIFIER)],
        input=json.dumps(payload),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    assert proc.returncode == 2
    assert proc.stdout == ""
    assert "ERROR:" in proc.stderr


def test_classifier_has_no_runtime_or_remediation_path() -> None:
    text = CLASSIFIER.read_text(encoding="utf-8")
    forbidden_code = (
        "import subprocess",
        "from subprocess",
        "os.system(",
        "subprocess.run(",
        "subprocess.Popen(",
        "systemctl restart",
        "systemctl reset-failed",
        "docker restart",
        "hermes cron run",
    )
    for token in forbidden_code:
        assert token not in text


if __name__ == "__main__":
    test_rdc_pending_auth_overrides_active()
    test_recovered_loop_oom_and_hermes_are_distinct()
    test_fail_closed_stale_and_not_ready_are_separate()
    test_invalid_input_fails_closed()
    test_classifier_has_no_runtime_or_remediation_path()
    print("Observability classifier tests: PASS")
