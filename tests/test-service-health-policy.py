#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
POLICY = ROOT / "ops/config/service-health.tsv"
FIXTURE = ROOT / "tests/fixtures/service-health/runtime-containers-2026-09-20.txt"

FIELDS = (
    "service_id", "container_name", "owner", "lifecycle", "required_state",
    "docker_health", "probe_type", "probe_target", "startup_grace_seconds",
    "attempts", "classification", "rationale",
)


def load_policy():
    rows = []
    for raw in POLICY.read_text(encoding="utf-8").splitlines():
        if not raw or raw.startswith("#"):
            continue
        parts = raw.split("\t")
        assert len(parts) == len(FIELDS), (raw, len(parts))
        rows.append(dict(zip(FIELDS, parts)))
    return rows


def test_policy_schema_and_uniqueness():
    rows = load_policy()
    assert rows
    assert len({r["service_id"] for r in rows}) == len(rows)
    assert len({r["container_name"] for r in rows}) == len(rows)
    for row in rows:
        assert row["lifecycle"] in {"production", "preview"}
        assert row["required_state"] == "running"
        assert row["docker_health"] in {"required", "absent"}
        assert row["probe_type"] in {"none", "http", "tcp", "exception"}
        assert row["classification"] in {"required", "observe"}
        assert int(row["startup_grace_seconds"]) > 0
        assert int(row["attempts"]) > 0
        assert row["rationale"].strip()
        if row["docker_health"] == "absent":
            assert row["probe_type"] != "none", row["service_id"]
        if row["probe_type"] in {"http", "tcp"}:
            assert row["probe_target"] != "-", row["service_id"]


def test_runtime_snapshot_is_fully_classified():
    rows = load_policy()
    by_container = {r["container_name"]: r for r in rows}
    runtime = [x for x in FIXTURE.read_text(encoding="utf-8").splitlines() if x]
    assert set(runtime) == set(by_container)
    assert by_container["rozkalns-weather-public-weather-1"]["classification"] == "observe"
    assert by_container["rozkalns-weather-public-weather-1"]["owner"] == "rozkalns_weather"
    for name in runtime:
        row = by_container[name]
        if row["lifecycle"] == "preview":
            assert row["classification"] == "observe"


def test_no_running_only_production_acceptance_without_explicit_exception():
    for row in load_policy():
        if row["lifecycle"] != "production":
            continue
        if row["docker_health"] == "required":
            continue
        assert row["probe_type"] in {"http", "tcp", "exception"}
        if row["probe_type"] == "exception":
            rationale = row["rationale"].lower()
            assert "running-only" in rationale or "process-only" in rationale


if __name__ == "__main__":
    test_policy_schema_and_uniqueness()
    test_runtime_snapshot_is_fully_classified()
    test_no_running_only_production_acceptance_without_explicit_exception()
    print("Service health policy tests: PASS")
