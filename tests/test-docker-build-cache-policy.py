#!/usr/bin/env python3
from __future__ import annotations

import importlib.machinery
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
POLICY = ROOT / "ops/lib/rpi5-docker-build-cache-policy.py"
CLI = ROOT / "ops/bin/rpi5-docker-build-cache-plan"

spec = importlib.util.spec_from_file_location("cache_policy", POLICY)
assert spec and spec.loader
policy = importlib.util.module_from_spec(spec)
spec.loader.exec_module(policy)

loader = importlib.machinery.SourceFileLoader("cache_plan", str(CLI))
cli_spec = importlib.util.spec_from_loader("cache_plan", loader)
assert cli_spec and cli_spec.loader
cli = importlib.util.module_from_spec(cli_spec)
cli_spec.loader.exec_module(cli)


def retention_plan(used: int, reclaimable: int, maximum: int) -> dict:
    return {
        "schema": "rpi5-docker-retention-plan-result.v1",
        "build_cache": {
            "bytes": used,
            "reclaimable_bytes": reclaimable,
            "max_bytes": maximum,
            "exceeded": used > maximum,
            "action": "report-only",
        },
    }


noop = policy.build_cache_plan(
    retention_plan(5_000, 4_000, 8_000), builder="default", min_age_seconds=1209600
)
assert noop["action"] == "noop"
assert noop["future_prune_argv"] is None

blocked = policy.build_cache_plan(
    retention_plan(10_000, 1_000, 8_000), builder="default", min_age_seconds=1209600
)
assert blocked["action"] == "blocked"
assert blocked["reason"] == "insufficient-reclaimable-cache-evidence"
assert blocked["future_prune_argv"] is None

planned = policy.build_cache_plan(
    retention_plan(10_000, 5_000, 8_000), builder="default", min_age_seconds=1209600
)
assert planned["action"] == "prune-required"
assert planned["policy"]["include_internal_frontend"] is False
argv = planned["future_prune_argv"]
assert argv == [
    "docker",
    "buildx",
    "--builder",
    "default",
    "prune",
    "--force",
    "--filter",
    "until=1209600s",
    "--filter",
    "inuse=false",
    "--filter",
    "shared=false",
    "--max-used-space",
    "8000B",
]
assert "--all" not in argv
assert "system" not in argv
assert "image" not in argv
assert "volume" not in argv

for bad in (
    retention_plan(10_000, 11_000, 8_000),
    {"schema": "wrong", "build_cache": {}},
):
    try:
        policy.build_cache_plan(bad, builder="default", min_age_seconds=1)
    except policy.CachePolicyError:
        pass
    else:
        raise AssertionError("invalid cache evidence was accepted")

contradict = retention_plan(10_000, 5_000, 8_000)
contradict["build_cache"]["exceeded"] = False
try:
    policy.build_cache_plan(contradict, builder="default", min_age_seconds=1)
except policy.CachePolicyError as exc:
    assert "contradicts" in str(exc)
else:
    raise AssertionError("contradictory exceeded flag was accepted")

try:
    policy.build_cache_plan(
        retention_plan(10_000, 5_000, 8_000), builder="../default", min_age_seconds=1
    )
except policy.CachePolicyError as exc:
    assert "builder identity" in str(exc)
else:
    raise AssertionError("unsafe builder identity was accepted")


class FakeRunner:
    def __init__(self, missing: str | None = None):
        self.missing = missing
        self.calls: list[list[str]] = []

    def run(self, argv):
        self.calls.append(list(argv))
        if argv == ["docker", "buildx", "--help"]:
            text = "--builder Override builder\n"
        elif argv == ["docker", "buildx", "prune", "--help"]:
            text = "--filter FILTER\n--force\n--max-used-space BYTES\n"
        elif argv == ["docker", "buildx", "inspect", "default"]:
            text = "Name: default\nDriver: docker\n"
        else:
            raise AssertionError(argv)
        if self.missing:
            text = text.replace(self.missing, "")
        return text


runner = FakeRunner()
cap = cli.require_capabilities(runner, "default")
assert cap["max_used_space"] is True
assert runner.calls == [
    ["docker", "buildx", "--help"],
    ["docker", "buildx", "prune", "--help"],
    ["docker", "buildx", "inspect", "default"],
]
assert all("prune" not in call or call[-1] == "--help" for call in runner.calls)

for missing in ("--builder", "--filter", "--max-used-space"):
    try:
        cli.require_capabilities(FakeRunner(missing=missing), "default")
    except cli.PlanError as exc:
        assert "capabilities missing" in str(exc)
    else:
        raise AssertionError(f"missing capability accepted: {missing}")

try:
    cli.ReadOnlyRunner(1).run(["docker", "buildx", "--builder", "default", "prune", "--force"])
except cli.PlanError as exc:
    assert "refusing non-read-only command" in str(exc)
else:
    raise AssertionError("mutating buildx prune command was accepted by read-only runner")

try:
    policy.build_cache_plan(retention_plan(10_000, 5_000, 8_000), builder="default", min_age_seconds=0)
except policy.CachePolicyError as exc:
    assert "must be positive" in str(exc)
else:
    raise AssertionError("zero min-age was accepted")


class WrongIdentityRunner(FakeRunner):
    def run(self, argv):
        text = super().run(argv)
        if argv == ["docker", "buildx", "inspect", "default"]:
            return "Name: other\nDriver: docker\n"
        return text


try:
    cli.require_capabilities(WrongIdentityRunner(), "default")
except cli.PlanError as exc:
    assert "identity mismatch" in str(exc)
else:
    raise AssertionError("builder identity mismatch was accepted")

source = CLI.read_text(encoding="utf-8")
policy_source = POLICY.read_text(encoding="utf-8")
for forbidden in (
    "docker system prune",
    "docker image prune",
    "docker volume prune",
    "docker container prune",
    "docker network prune",
):
    assert forbidden not in source
    assert forbidden not in policy_source
assert '"--all"' not in policy_source

print("Docker build-cache storage policy tests: PASS")
