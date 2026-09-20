#!/usr/bin/env python3
from __future__ import annotations

import importlib.machinery
import importlib.util
import json
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXECUTOR = ROOT / "ops/bin/rpi5-docker-retention-executor"
loader = importlib.machinery.SourceFileLoader("retention_executor", str(EXECUTOR))
spec = importlib.util.spec_from_loader("retention_executor", loader)
assert spec and spec.loader
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def sid(ch: str) -> str:
    return "sha256:" + ch * 64


CURRENT = sid("1")
PREVIOUS = sid("2")
TARGET = sid("3")
LINEAGE = "ghcr.io/example/app"


def reviewed_plan() -> dict:
    return {
        "schema": "rpi5-docker-retention-plan-result.v1",
        "watermark": {"root_used_percent": 46, "high_percent": 80, "exceeded": False},
        "build_cache": {
            "bytes": 100,
            "reclaimable_bytes": 50,
            "max_bytes": 1000,
            "exceeded": False,
            "action": "report-only",
        },
        "summary": {
            "images": 3,
            "delete": 1,
            "delete_bytes": 10,
            "protect": 2,
            "block": 0,
            "ignore": 0,
            "named_volumes": 0,
            "anonymous_volumes": 0,
        },
        "blocked_lineages": {},
        "services": [
            {
                "key": "main/web",
                "project": "main",
                "service": "web",
                "lineage": LINEAGE,
                "current_id": CURRENT,
                "candidate_ids": [],
                "previous_known_good_ids": [PREVIOUS],
            }
        ],
        "images": [
            {
                "id": CURRENT,
                "action": "protect",
                "role": "container-referenced",
                "reasons": ["referenced-by-container"],
                "lineages": [LINEAGE],
                "created_epoch": 100,
                "size_bytes": 10,
                "repositories": [LINEAGE],
                "container_refs": ["main-web-1"],
            },
            {
                "id": PREVIOUS,
                "action": "protect",
                "role": "previous-known-good",
                "reasons": ["protected-identity"],
                "lineages": [LINEAGE],
                "created_epoch": 90,
                "size_bytes": 10,
                "repositories": [LINEAGE],
                "container_refs": [],
            },
            {
                "id": TARGET,
                "action": "delete",
                "role": "superseded",
                "reasons": ["eligible-by-age", "beyond-count-reserve"],
                "lineages": [LINEAGE],
                "created_epoch": 80,
                "size_bytes": 10,
                "repositories": [LINEAGE],
                "container_refs": [],
            },
        ],
        "delete_ids": [TARGET],
        "volumes": [],
    }


class FakeReport:
    @staticmethod
    def parse_array(text, _ctx):
        return json.loads(text)

    @staticmethod
    def repo_root(ref):
        if "@" in ref:
            return ref.split("@", 1)[0]
        slash = ref.rfind("/")
        colon = ref.rfind(":")
        return ref[:colon] if colon > slash else ref


class FakeRunner:
    def __init__(self, tags=None, digests=None, present=True):
        self.tags = [f"{LINEAGE}:old"] if tags is None else tags
        self.digests = [f"{LINEAGE}@sha256:" + "a" * 64] if digests is None else digests
        self.present = present

    def run(self, argv):
        if argv == ["docker", "image", "inspect", TARGET]:
            return json.dumps(
                [{"Id": TARGET, "RepoTags": self.tags, "RepoDigests": self.digests}]
            )
        if argv == ["docker", "image", "ls", "-a", "--no-trunc", "--quiet"]:
            return (TARGET + "\n") if self.present else ""
        raise AssertionError(argv)


plan = reviewed_plan()
decisions = mod.validate_reviewed_plan(plan, [TARGET])
assert decisions[TARGET]["action"] == "delete"
assert mod.safety_fingerprint(plan) == mod.safety_fingerprint(dict(plan))

fresh = json.loads(json.dumps(plan))
mod.assert_initial_freshness(plan, fresh)
assert mod.assert_target_still_deletable(plan, fresh, TARGET)["action"] == "delete"

changed = json.loads(json.dumps(plan))
changed["services"][0]["current_id"] = sid("9")
try:
    mod.assert_target_still_deletable(plan, changed, TARGET)
except mod.ExecutorError as exc:
    assert "protection changed" in str(exc)
else:
    raise AssertionError("protection drift was accepted")

changed = json.loads(json.dumps(plan))
next(item for item in changed["images"] if item["id"] == TARGET)["action"] = "protect"
changed["delete_ids"] = []
try:
    mod.assert_target_still_deletable(plan, changed, TARGET)
except mod.ExecutorError as exc:
    assert "no longer in fresh delete_ids" in str(exc)
else:
    raise AssertionError("target drift was accepted")

inspect = mod.inspect_exact_target(FakeReport, FakeRunner(), TARGET, LINEAGE)
assert inspect["lineage"] == LINEAGE

try:
    mod.inspect_exact_target(
        FakeReport,
        FakeRunner(tags=[f"{LINEAGE}:old", f"{LINEAGE}:older"]),
        TARGET,
        LINEAGE,
    )
except mod.ExecutorError as exc:
    assert "multiple RepoTags" in str(exc)
else:
    raise AssertionError("multi-tag target was accepted")

try:
    mod.inspect_exact_target(
        FakeReport,
        FakeRunner(tags=[f"{LINEAGE}:old", "ghcr.io/other/app:old"]),
        TARGET,
        LINEAGE,
    )
except mod.ExecutorError as exc:
    assert "cross-repository ownership" in str(exc)
else:
    raise AssertionError("cross-repository target was accepted")

assert mod.delete_argv(TARGET) == [
    "docker",
    "image",
    "rm",
    "--no-prune",
    TARGET,
]
assert "--force" not in mod.delete_argv(TARGET)

try:
    mod.validate_reviewed_plan(plan, [CURRENT])
except mod.ExecutorError as exc:
    assert "not in reviewed delete_ids" in str(exc)
else:
    raise AssertionError("protected target was accepted")

cross = reviewed_plan()
next(item for item in cross["images"] if item["id"] == TARGET)["repositories"].append("ghcr.io/other/app")
try:
    mod.validate_reviewed_plan(cross, [TARGET])
except mod.ExecutorError as exc:
    assert "cross-repository ownership" in str(exc)
else:
    raise AssertionError("cross-repository reviewed plan was accepted")

with tempfile.TemporaryDirectory() as td:
    root = Path(td)
    plan_path = root / "plan.json"
    raw = json.dumps(plan, sort_keys=True).encode()
    plan_path.write_bytes(raw)
    digest = __import__("hashlib").sha256(raw).hexdigest()
    loaded, actual = mod.read_reviewed_plan(plan_path, digest)
    assert loaded == plan and actual == digest
    try:
        mod.read_reviewed_plan(plan_path, "0" * 64)
    except mod.ExecutorError as exc:
        assert "SHA256 mismatch" in str(exc)
    else:
        raise AssertionError("plan hash mismatch was accepted")

    evidence = root / "evidence.jsonl"
    writer = mod.EvidenceWriter(evidence)
    writer.write({"event": "test", "id": TARGET})
    writer.close()
    assert json.loads(evidence.read_text())["event"] == "test"
    assert evidence.stat().st_mode & 0o777 == 0o600


# run_executor is fail-closed and never calls the delete function in dry-run.
original_fresh_plan = mod.fresh_plan
original_inspect = mod.inspect_exact_target
original_absent = mod.assert_image_absent
try:
    mod.fresh_plan = lambda *args, **kwargs: reviewed_plan()
    mod.inspect_exact_target = lambda *args, **kwargs: {
        "id": TARGET,
        "lineage": LINEAGE,
        "repo_tags": [f"{LINEAGE}:old"],
        "repo_digests": [f"{LINEAGE}@sha256:" + "a" * 64],
    }
    mod.assert_image_absent = lambda *args, **kwargs: None
    calls = []

    dry = mod.run_executor(
        reviewed_plan(),
        [TARGET],
        plan_sha256="a" * 64,
        report_mod=type("R", (), {"Runner": lambda _timeout: object()}),
        inventory_mod=object(),
        planner_mod=object(),
        projects=[("main", Path("/main")), ("cv", Path("/cv"))],
        evidence_root=Path("/evidence"),
        trusted_runs=["20260920_022000"],
        retention_seconds=100,
        reserve=0,
        timeout_seconds=10,
        apply=False,
        evidence_output=None,
        delete_func=lambda *args: calls.append(args),
    )
    assert dry["mode"] == "dry-run"
    assert dry["results"][0]["status"] == "would-delete"
    assert calls == []

    with tempfile.TemporaryDirectory() as td:
        ev = Path(td) / "apply.jsonl"

        def fake_delete(image_id, timeout):
            calls.append((image_id, timeout))
            return {"argv": mod.delete_argv(image_id), "rc": 0, "stdout": "Deleted"}

        applied = mod.run_executor(
            reviewed_plan(),
            [TARGET],
            plan_sha256="b" * 64,
            report_mod=type("R", (), {"Runner": lambda _timeout: object()}),
            inventory_mod=object(),
            planner_mod=object(),
            projects=[("main", Path("/main")), ("cv", Path("/cv"))],
            evidence_root=Path("/evidence"),
            trusted_runs=["20260920_022000"],
            retention_seconds=100,
            reserve=0,
            timeout_seconds=10,
            apply=True,
            evidence_output=ev,
            delete_func=fake_delete,
        )
        assert applied["results"][0]["status"] == "deleted"
        assert calls[-1] == (TARGET, 10)
        events = [json.loads(line) for line in ev.read_text().splitlines()]
        assert events[0]["event"] == "executor-start"
        assert any(event["event"] == "pre-delete-approved" for event in events)
        assert any(event["event"] == "delete-succeeded" for event in events)
        assert all(event.get("retry_attempted", False) is False for event in events)
finally:
    mod.fresh_plan = original_fresh_plan
    mod.inspect_exact_target = original_inspect
    mod.assert_image_absent = original_absent


# Fresh collector/planner failures are normalized into deterministic ExecutorError.
class FailingReport:
    class ReportError(RuntimeError):
        pass

    class Runner:
        def __init__(self, _timeout):
            pass

    @staticmethod
    def collect_raw(*args, **kwargs):
        raise FailingReport.ReportError("timeout")

try:
    mod.fresh_plan(
        FailingReport,
        object(),
        object(),
        projects=[],
        evidence_root=Path("/evidence"),
        trusted_runs=["20260920_022000"],
        retention_seconds=100,
        reserve=0,
        high_percent=80,
        cache_max_bytes=1000,
        timeout_seconds=1,
    )
except mod.ExecutorError as exc:
    assert "fresh runtime replan failed: timeout" in str(exc)
else:
    raise AssertionError("fresh report failure escaped fail-closed normalization")

source = EXECUTOR.read_text(encoding="utf-8")
for forbidden in ("docker system prune", "docker image prune -a", "docker volume prune"):
    assert forbidden not in source
assert '"--force"' not in source

print("Docker retention exact-image executor tests: PASS")
