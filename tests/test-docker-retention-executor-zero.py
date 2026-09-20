#!/usr/bin/env python3
from __future__ import annotations

import importlib.machinery
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXECUTOR = ROOT / "ops/bin/rpi5-docker-retention-executor"
loader = importlib.machinery.SourceFileLoader("retention_executor_zero", str(EXECUTOR))
spec = importlib.util.spec_from_loader("retention_executor_zero", loader)
assert spec and spec.loader
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def sid(ch: str) -> str:
    return "sha256:" + ch * 64


CURRENT = sid("1")
LINEAGE = "ghcr.io/example/app"


def zero_delete_plan() -> dict:
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
            "images": 1,
            "delete": 0,
            "delete_bytes": 0,
            "protect": 1,
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
                "previous_known_good_ids": [],
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
            }
        ],
        "delete_ids": [],
        "volumes": [],
    }


plan = zero_delete_plan()
original_fresh_plan = mod.fresh_plan
fresh_calls = 0

try:
    def fake_fresh_plan(*args, **kwargs):
        global fresh_calls
        fresh_calls += 1
        return json.loads(json.dumps(plan))

    mod.fresh_plan = fake_fresh_plan

    dry = mod.run_executor(
        plan,
        [],
        plan_sha256="a" * 64,
        report_mod=type("R", (), {"Runner": lambda _timeout: object()}),
        inventory_mod=object(),
        planner_mod=object(),
        projects=[("main", Path("/main")), ("cv", Path("/cv"))],
        evidence_root=Path("/evidence"),
        trusted_runs=["20260920_022000"],
        retention_seconds=100,
        reserve=1,
        timeout_seconds=10,
        apply=False,
        evidence_output=None,
    )

    assert fresh_calls == 1
    assert dry["schema"] == "rpi5-docker-retention-executor-result.v1"
    assert dry["mode"] == "dry-run"
    assert dry["requested_delete_ids"] == []
    assert dry["results"] == []
    assert dry["fresh_safety_fingerprint_sha256"] == mod.safety_fingerprint(plan)

    try:
        mod.run_executor(
            plan,
            [],
            plan_sha256="b" * 64,
            report_mod=type("R", (), {"Runner": lambda _timeout: object()}),
            inventory_mod=object(),
            planner_mod=object(),
            projects=[("main", Path("/main")), ("cv", Path("/cv"))],
            evidence_root=Path("/evidence"),
            trusted_runs=["20260920_022000"],
            retention_seconds=100,
            reserve=1,
            timeout_seconds=10,
            apply=True,
            evidence_output=Path("/must-not-be-created"),
        )
    except mod.ExecutorError as exc:
        assert "at least one explicit delete id is required with --apply" in str(exc)
    else:
        raise AssertionError("empty apply target set was accepted")

    assert fresh_calls == 1
finally:
    mod.fresh_plan = original_fresh_plan

print("Docker retention zero-delete dry-run contract: PASS")
