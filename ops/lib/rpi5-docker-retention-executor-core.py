#!/usr/bin/env python3
"""Pure fail-closed validation primitives for exact-image-ID retention execution."""
from __future__ import annotations

import hashlib
import json
import os
import re
from pathlib import Path
from typing import Any

PLAN_SCHEMA = "rpi5-docker-retention-plan-result.v1"
RESULT_SCHEMA = "rpi5-docker-retention-executor-result.v1"
IMAGE_ID_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
HEX64_RE = re.compile(r"^[0-9a-f]{64}$")

class ExecutorError(RuntimeError):
    pass


class DeleteError(ExecutorError):
    def __init__(self, image_id: str, rc: int, stdout: str, stderr: str):
        super().__init__(f"docker image rm failed for {image_id}: rc={rc}")
        self.image_id = image_id
        self.rc = rc
        self.stdout = stdout
        self.stderr = stderr


def require_image_id(value: Any, context: str) -> str:
    if not isinstance(value, str) or not IMAGE_ID_RE.fullmatch(value):
        raise ExecutorError(f"invalid image id for {context}: {value!r}")
    return value


def canonical_json(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def fingerprint(value: Any) -> str:
    return hashlib.sha256(canonical_json(value)).hexdigest()


def read_reviewed_plan(path: Path, expected_sha256: str) -> tuple[dict[str, Any], str]:
    if not path.is_file() or path.is_symlink():
        raise ExecutorError(f"planner result missing/unsafe: {path}")
    if not HEX64_RE.fullmatch(expected_sha256):
        raise ExecutorError("expected plan SHA256 must be 64 lowercase hex characters")
    try:
        raw = path.read_bytes()
    except OSError as exc:
        raise ExecutorError(f"cannot read planner result: {path}: {exc}") from exc
    actual = hashlib.sha256(raw).hexdigest()
    if actual != expected_sha256:
        raise ExecutorError(f"planner result SHA256 mismatch: expected {expected_sha256}, got {actual}")
    try:
        value = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ExecutorError(f"planner result is invalid JSON: {exc}") from exc
    if not isinstance(value, dict):
        raise ExecutorError("planner result must be a JSON object")
    return value, actual


def decisions_by_id(plan: dict[str, Any]) -> dict[str, dict[str, Any]]:
    images = plan.get("images")
    if not isinstance(images, list):
        raise ExecutorError("planner result images must be an array")
    out: dict[str, dict[str, Any]] = {}
    for index, item in enumerate(images):
        if not isinstance(item, dict):
            raise ExecutorError(f"planner result images[{index}] must be an object")
        image_id = require_image_id(item.get("id"), f"planner result images[{index}]")
        if image_id in out:
            raise ExecutorError(f"duplicate planner image id: {image_id}")
        out[image_id] = item
    return out


def validate_reviewed_plan(plan: dict[str, Any], requested_ids: list[str]) -> dict[str, dict[str, Any]]:
    if plan.get("schema") != PLAN_SCHEMA:
        raise ExecutorError(f"planner result schema must be {PLAN_SCHEMA}")

    delete_ids_raw = plan.get("delete_ids")
    if not isinstance(delete_ids_raw, list):
        raise ExecutorError("planner result delete_ids must be an array")
    delete_ids = [require_image_id(item, "planner result delete_ids") for item in delete_ids_raw]
    if delete_ids != sorted(set(delete_ids)):
        raise ExecutorError("planner result delete_ids must be unique and sorted")

    requested = [require_image_id(item, "requested delete id") for item in requested_ids]
    if requested != list(dict.fromkeys(requested)):
        raise ExecutorError("requested delete ids must be unique")

    decisions = decisions_by_id(plan)
    for image_id in requested:
        if image_id not in delete_ids:
            raise ExecutorError(f"requested image is not in reviewed delete_ids: {image_id}")
        decision = decisions.get(image_id)
        if decision is None:
            raise ExecutorError(f"requested image has no planner decision: {image_id}")
        if decision.get("action") != "delete" or decision.get("role") != "superseded":
            raise ExecutorError(f"requested image is not a superseded delete decision: {image_id}")
        lineages = decision.get("lineages")
        repos = decision.get("repositories")
        refs = decision.get("container_refs")
        if not isinstance(lineages, list) or len(lineages) != 1 or not all(isinstance(x, str) and x for x in lineages):
            raise ExecutorError(f"requested image must map to one managed lineage: {image_id}")
        if not isinstance(repos, list) or not all(isinstance(x, str) and x for x in repos):
            raise ExecutorError(f"invalid repositories for requested image: {image_id}")
        if set(repos) != {lineages[0]}:
            raise ExecutorError(f"cross-repository ownership blocks deletion: {image_id}")
        if refs != []:
            raise ExecutorError(f"container-referenced image cannot be deleted: {image_id}")

    services = plan.get("services")
    blocked = plan.get("blocked_lineages")
    watermark = plan.get("watermark")
    cache = plan.get("build_cache")
    if not isinstance(services, list) or not isinstance(blocked, dict):
        raise ExecutorError("planner result services/blocked_lineages are invalid")
    if not isinstance(watermark, dict) or not isinstance(watermark.get("high_percent"), int):
        raise ExecutorError("planner result watermark is invalid")
    if not isinstance(cache, dict) or not isinstance(cache.get("max_bytes"), int):
        raise ExecutorError("planner result build_cache is invalid")

    return decisions


def safety_view(plan: dict[str, Any]) -> dict[str, Any]:
    """Return only deletion-safety state; capacity/report-only fields are excluded."""
    return {
        "schema": plan.get("schema"),
        "services": plan.get("services"),
        "blocked_lineages": plan.get("blocked_lineages"),
        "images": plan.get("images"),
        "delete_ids": plan.get("delete_ids"),
    }


def safety_fingerprint(plan: dict[str, Any]) -> str:
    return fingerprint(safety_view(plan))


def assert_initial_freshness(reviewed: dict[str, Any], fresh: dict[str, Any]) -> None:
    if safety_view(reviewed) != safety_view(fresh):
        raise ExecutorError(
            "planner evidence is stale: fresh runtime safety state differs from reviewed planner result"
        )


def target_decision(plan: dict[str, Any], image_id: str) -> dict[str, Any]:
    decision = decisions_by_id(plan).get(image_id)
    if decision is None:
        raise ExecutorError(f"target image is missing from fresh planner result: {image_id}")
    return decision


def assert_target_still_deletable(
    reviewed: dict[str, Any],
    fresh: dict[str, Any],
    image_id: str,
) -> dict[str, Any]:
    if fresh.get("schema") != PLAN_SCHEMA:
        raise ExecutorError("fresh planner result has unexpected schema")
    if fresh.get("services") != reviewed.get("services"):
        raise ExecutorError("current/candidate/previous-known-good protection changed since planning")

    old = target_decision(reviewed, image_id)
    new = target_decision(fresh, image_id)
    if image_id not in fresh.get("delete_ids", []):
        raise ExecutorError(f"target is no longer in fresh delete_ids: {image_id}")
    if new.get("action") != "delete" or new.get("role") != "superseded":
        raise ExecutorError(f"target is no longer a superseded delete decision: {image_id}")
    if new.get("container_refs") != []:
        raise ExecutorError(f"target is now container-referenced: {image_id}")
    if new.get("lineages") != old.get("lineages"):
        raise ExecutorError(f"target lineage changed since planning: {image_id}")
    if new.get("repositories") != old.get("repositories"):
        raise ExecutorError(f"target repository ownership changed since planning: {image_id}")
    if len(new.get("lineages", [])) != 1 or set(new.get("repositories", [])) != {new["lineages"][0]}:
        raise ExecutorError(f"target ownership is no longer unambiguous: {image_id}")
    return new


def inspect_exact_target(report_mod, runner, image_id: str, lineage: str) -> dict[str, Any]:
    rows = report_mod.parse_array(
        runner.run(["docker", "image", "inspect", image_id]),
        f"docker image inspect {image_id}",
    )
    if len(rows) != 1 or not isinstance(rows[0], dict):
        raise ExecutorError(f"expected one image inspect result for {image_id}")
    row = rows[0]
    if require_image_id(row.get("Id"), f"docker image inspect {image_id}") != image_id:
        raise ExecutorError(f"image identity changed during pre-delete inspection: {image_id}")

    tags = row.get("RepoTags") or []
    digests = row.get("RepoDigests") or []
    if not isinstance(tags, list) or not isinstance(digests, list):
        raise ExecutorError(f"RepoTags/RepoDigests must be arrays for {image_id}")
    refs: list[str] = []
    for value in [*tags, *digests]:
        if not isinstance(value, str) or not value or value == "<none>:<none>":
            raise ExecutorError(f"invalid repository reference for {image_id}: {value!r}")
        refs.append(value)
    if not refs:
        raise ExecutorError(f"target has no repository ownership evidence: {image_id}")

    roots = {report_mod.repo_root(value) for value in refs}
    if roots != {lineage}:
        raise ExecutorError(f"cross-repository ownership detected at pre-delete: {image_id}")
    if len(tags) > 1:
        raise ExecutorError(
            f"multiple RepoTags block exact-ID deletion without --force: {image_id}"
        )
    return {
        "id": image_id,
        "lineage": lineage,
        "repo_tags": sorted(tags),
        "repo_digests": sorted(digests),
    }


def delete_argv(image_id: str) -> list[str]:
    require_image_id(image_id, "delete command")
    # --no-prune prevents collateral removal of untagged parent images.
    return ["docker", "image", "rm", "--no-prune", image_id]


class EvidenceWriter:
    def __init__(self, path: Path):
        if not path.is_absolute():
            raise ExecutorError("apply evidence output must be an absolute path")
        parent = path.parent
        if not parent.is_dir() or parent.is_symlink():
            raise ExecutorError(f"apply evidence parent missing/unsafe: {parent}")
        flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
        if hasattr(os, "O_NOFOLLOW"):
            flags |= os.O_NOFOLLOW
        try:
            self.fd = os.open(path, flags, 0o600)
        except OSError as exc:
            raise ExecutorError(f"cannot create apply evidence file: {path}: {exc}") from exc
        self.path = path

    def write(self, event: dict[str, Any]) -> None:
        data = canonical_json(event) + b"\n"
        try:
            os.write(self.fd, data)
            os.fsync(self.fd)
        except OSError as exc:
            raise ExecutorError(f"cannot persist apply evidence to {self.path}: {exc}") from exc

    def close(self) -> None:
        if getattr(self, "fd", -1) >= 0:
            os.close(self.fd)
            self.fd = -1
