#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
PLANNER = ROOT / "ops/lib/rpi5-docker-retention-plan.py"


def image_id(label: str) -> str:
    return "sha256:" + hashlib.sha256(label.encode("utf-8")).hexdigest()


def image(label: str, age: int, repo: str | None, *, refs: list[str] | None = None, size: int = 100) -> dict:
    return {
        "id": image_id(label),
        "created_epoch": 2_000_000 - age,
        "size_bytes": size,
        "repositories": [] if repo is None else [repo],
        "container_refs": refs or [],
    }


def run_plan(payload: dict, *, expect_ok: bool = True) -> tuple[subprocess.CompletedProcess[str], dict | None]:
    proc = subprocess.run(
        ["python3", str(PLANNER)],
        input=json.dumps(payload),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if expect_ok:
        assert proc.returncode == 0, proc.stderr
        return proc, json.loads(proc.stdout)
    assert proc.returncode == 2
    return proc, None


def base_payload() -> dict:
    return {
        "schema": "rpi5-docker-retention-plan.v1",
        "now_epoch": 2_000_000,
        "retention_seconds": 1_000,
        "superseded_keep_per_lineage": 1,
        "root_used_percent": 46,
        "disk_high_watermark_percent": 80,
        "images": [
            image("a", 100, "repo/app", refs=["project_app_1"]),
            image("b", 50, "repo/app"),
            image("c", 2_000, "repo/app"),
            image("d", 3_000, "repo/app"),
            image("e", 4_000, "repo/app", size=500),
            image("f", 500, "repo/app"),
            image("g", 4_000, "repo/unmanaged"),
            image("h", 4_000, None),
        ],
        "services": [
            {
                "project": "project",
                "service": "app",
                "lineage": "repo/app",
                "current_id": image_id("a"),
                "candidate_ids": [image_id("b")],
                "previous_known_good_ids": [image_id("c")],
            }
        ],
        "volumes": [
            {"name": "project_data", "project": "project", "kind": "named"},
            {"name": "anon-1", "project": None, "kind": "anonymous"},
        ],
        "build_cache": {
            "bytes": 5_000,
            "reclaimable_bytes": 4_000,
            "max_bytes": 2_000,
        },
    }


def decision(result: dict, label: str) -> dict:
    return next(item for item in result["images"] if item["id"] == image_id(label))


def test_happy_path() -> None:
    _, result = run_plan(base_payload())
    assert result is not None
    assert decision(result, "a")["action"] == "protect"
    assert decision(result, "a")["role"] == "container-referenced"
    assert decision(result, "b")["role"] == "candidate"
    assert decision(result, "c")["role"] == "previous-known-good"
    assert decision(result, "d")["role"] == "count-reserve"
    assert decision(result, "e")["action"] == "delete"
    assert decision(result, "f")["role"] == "young"
    assert decision(result, "g")["role"] == "unmanaged"
    assert decision(result, "h")["role"] == "dangling"
    assert result["delete_ids"] == [image_id("e")]
    assert result["summary"]["delete_bytes"] == 500
    assert result["summary"]["named_volumes"] == 1
    assert result["summary"]["anonymous_volumes"] == 1
    assert result["build_cache"]["exceeded"] is True
    assert result["build_cache"]["action"] == "report-only"
    assert result["watermark"]["exceeded"] is False
    assert all(volume["action"] == "report-only" for volume in result["volumes"])


def test_missing_previous_good_blocks_lineage() -> None:
    payload = base_payload()
    payload["services"][0]["previous_known_good_ids"] = []
    _, result = run_plan(payload)
    assert result is not None
    assert result["blocked_lineages"] == {"repo/app": ["missing-previous-known-good"]}
    assert decision(result, "d")["action"] == "block"
    assert decision(result, "e")["action"] == "block"
    assert result["delete_ids"] == []


def test_shared_lineage_across_services_blocks_old_images() -> None:
    payload = base_payload()
    payload["images"].extend(
        [
            image("i", 100, "repo/app", refs=["project_worker_1"]),
            image("j", 2_500, "repo/app"),
        ]
    )
    payload["services"].append(
        {
            "project": "project",
            "service": "worker",
            "lineage": "repo/app",
            "current_id": image_id("i"),
            "candidate_ids": [],
            "previous_known_good_ids": [image_id("j")],
        }
    )
    _, result = run_plan(payload)
    assert result is not None
    assert "shared-lineage-across-services" in result["blocked_lineages"]["repo/app"]
    assert decision(result, "e")["action"] == "block"
    assert result["delete_ids"] == []


def test_multi_lineage_image_is_ambiguous() -> None:
    payload = base_payload()
    payload["images"].extend(
        [
            image("i", 100, "repo/other", refs=["other_app_1"]),
            image("j", 2_000, "repo/other"),
            {
                "id": image_id("k"),
                "created_epoch": 1_990_000,
                "size_bytes": 100,
                "repositories": ["repo/app", "repo/other"],
                "container_refs": [],
            },
        ]
    )
    payload["services"].append(
        {
            "project": "other",
            "service": "app",
            "lineage": "repo/other",
            "current_id": image_id("i"),
            "candidate_ids": [],
            "previous_known_good_ids": [image_id("j")],
        }
    )
    _, result = run_plan(payload)
    assert result is not None
    assert decision(result, "k")["action"] == "block"
    assert "multiple-managed-lineages" in decision(result, "k")["reasons"]


def test_current_must_be_container_referenced() -> None:
    payload = base_payload()
    decision_image = next(item for item in payload["images"] if item["id"] == image_id("a"))
    decision_image["container_refs"] = []
    proc, _ = run_plan(payload, expect_ok=False)
    assert "current image is not container-referenced" in proc.stderr


def test_planner_has_no_execution_path() -> None:
    text = PLANNER.read_text(encoding="utf-8")
    for forbidden in ("docker image rm", "docker system prune", "docker volume prune", "subprocess"):
        assert forbidden not in text


if __name__ == "__main__":
    test_happy_path()
    test_missing_previous_good_blocks_lineage()
    test_shared_lineage_across_services_blocks_old_images()
    test_multi_lineage_image_is_ambiguous()
    test_current_must_be_container_referenced()
    test_planner_has_no_execution_path()
    print("Docker retention planner tests: PASS")
