#!/usr/bin/env python3
"""Pure adapter from sanitized runtime inventory to retention-planner input.

The adapter performs no Docker/systemd/filesystem mutation and does not invoke
Docker. Runtime collection is intentionally outside this module.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from typing import Any

INPUT_SCHEMA = "rpi5-docker-runtime-inventory.v1"
OUTPUT_SCHEMA = "rpi5-docker-retention-plan.v1"
IMAGE_ID_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
TOKEN_RE = re.compile(r"^[A-Za-z0-9._:-]+$")


def _obj(value: Any, context: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{context} must be an object")
    return value


def _list(value: Any, context: str) -> list[Any]:
    if not isinstance(value, list):
        raise ValueError(f"{context} must be an array")
    return value


def _token(value: Any, context: str) -> str:
    if not isinstance(value, str) or not value or not TOKEN_RE.fullmatch(value):
        raise ValueError(f"invalid token for {context}: {value!r}")
    return value


def _image_id(value: Any, context: str) -> str:
    if not isinstance(value, str) or not IMAGE_ID_RE.fullmatch(value):
        raise ValueError(f"invalid image id for {context}: {value!r}")
    return value


def _int(value: Any, context: str, *, minimum: int = 0, maximum: int | None = None) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value < minimum:
        raise ValueError(f"invalid integer for {context}: {value!r}")
    if maximum is not None and value > maximum:
        raise ValueError(f"invalid integer for {context}: {value!r}")
    return value


def _repositories(value: Any, context: str) -> list[str]:
    values = _list(value, context)
    repos = [_token(item, context) for item in values]
    return sorted(set(repos))


def build_inventory(payload: dict[str, Any]) -> dict[str, Any]:
    if payload.get("schema") != INPUT_SCHEMA:
        raise ValueError(f"schema must be {INPUT_SCHEMA}")

    policy = _obj(payload.get("policy"), "policy")
    now_epoch = _int(policy.get("now_epoch"), "policy.now_epoch", minimum=1)
    retention_seconds = _int(policy.get("retention_seconds"), "policy.retention_seconds")
    reserve = _int(policy.get("superseded_keep_per_lineage"), "policy.superseded_keep_per_lineage")
    root_used = _int(policy.get("root_used_percent"), "policy.root_used_percent", maximum=100)
    high_watermark = _int(policy.get("disk_high_watermark_percent"), "policy.disk_high_watermark_percent", minimum=1, maximum=100)

    images: dict[str, dict[str, Any]] = {}
    for index, item in enumerate(_list(payload.get("images"), "images")):
        raw = _obj(item, f"images[{index}]")
        image_id = _image_id(raw.get("id"), f"images[{index}].id")
        if image_id in images:
            raise ValueError(f"duplicate image id: {image_id}")
        images[image_id] = {
            "id": image_id,
            "created_epoch": _int(raw.get("created_epoch"), f"images[{index}].created_epoch"),
            "size_bytes": _int(raw.get("size_bytes"), f"images[{index}].size_bytes"),
            "repositories": _repositories(raw.get("repositories", []), f"images[{index}].repositories"),
            "container_refs": [],
        }

    containers: dict[str, str] = {}
    for index, item in enumerate(_list(payload.get("containers"), "containers")):
        raw = _obj(item, f"containers[{index}]")
        name = _token(raw.get("name"), f"containers[{index}].name")
        image_id = _image_id(raw.get("image_id"), f"containers[{index}].image_id")
        if name in containers:
            raise ValueError(f"duplicate container name: {name}")
        if image_id not in images:
            raise ValueError(f"container {name} references unknown image: {image_id}")
        containers[name] = image_id
        images[image_id]["container_refs"].append(name)

    for image in images.values():
        image["container_refs"] = sorted(image["container_refs"])

    rollback: dict[tuple[str, str], set[str]] = {}
    for index, item in enumerate(_list(payload.get("rollback_evidence", []), "rollback_evidence")):
        raw = _obj(item, f"rollback_evidence[{index}]")
        project = _token(raw.get("project"), f"rollback_evidence[{index}].project")
        service = _token(raw.get("service"), f"rollback_evidence[{index}].service")
        source = _token(raw.get("source"), f"rollback_evidence[{index}].source")
        phase = _token(raw.get("phase"), f"rollback_evidence[{index}].phase")
        outcome = _token(raw.get("outcome"), f"rollback_evidence[{index}].outcome")
        image_id = _image_id(raw.get("image_id"), f"rollback_evidence[{index}].image_id")
        if image_id not in images:
            raise ValueError(f"rollback evidence references unknown image: {image_id}")
        if source == "v28-compose-evidence" and phase == "pre-mutation" and outcome == "success":
            rollback.setdefault((project, service), set()).add(image_id)

    services: list[dict[str, Any]] = []
    service_keys: set[tuple[str, str]] = set()
    for index, item in enumerate(_list(payload.get("managed_services"), "managed_services")):
        raw = _obj(item, f"managed_services[{index}]")
        project = _token(raw.get("project"), f"managed_services[{index}].project")
        service = _token(raw.get("service"), f"managed_services[{index}].service")
        lineage = _token(raw.get("lineage"), f"managed_services[{index}].lineage")
        current_container = _token(raw.get("current_container"), f"managed_services[{index}].current_container")
        key = (project, service)
        if key in service_keys:
            raise ValueError(f"duplicate managed service: {project}/{service}")
        service_keys.add(key)
        if current_container not in containers:
            raise ValueError(f"missing current container for {project}/{service}: {current_container}")
        current_id = containers[current_container]
        if lineage not in images[current_id]["repositories"]:
            raise ValueError(f"current image outside lineage for {project}/{service}")

        candidate_raw = _list(raw.get("candidate_ids", []), f"managed_services[{index}].candidate_ids")
        candidate_ids = sorted({_image_id(value, f"managed_services[{index}].candidate_ids") for value in candidate_raw})
        for image_id in candidate_ids:
            if image_id not in images:
                raise ValueError(f"candidate image unknown for {project}/{service}: {image_id}")
            if lineage not in images[image_id]["repositories"]:
                raise ValueError(f"candidate image outside lineage for {project}/{service}: {image_id}")

        previous_ids = sorted(rollback.get(key, set()))
        previous_ids = [image_id for image_id in previous_ids if lineage in images[image_id]["repositories"]]

        services.append({
            "project": project,
            "service": service,
            "lineage": lineage,
            "current_id": current_id,
            "candidate_ids": candidate_ids,
            "previous_known_good_ids": previous_ids,
        })

    volumes: list[dict[str, Any]] = []
    for index, item in enumerate(_list(payload.get("volumes", []), "volumes")):
        raw = _obj(item, f"volumes[{index}]")
        name = _token(raw.get("name"), f"volumes[{index}].name")
        kind = _token(raw.get("kind"), f"volumes[{index}].kind")
        if kind not in {"named", "anonymous"}:
            raise ValueError(f"invalid volume kind for {name}: {kind}")
        project_value = raw.get("project")
        project = None if project_value is None else _token(project_value, f"volumes[{index}].project")
        volumes.append({"name": name, "project": project, "kind": kind})

    build_cache_raw = _obj(payload.get("build_cache"), "build_cache")
    build_cache = {
        "bytes": _int(build_cache_raw.get("bytes"), "build_cache.bytes"),
        "reclaimable_bytes": _int(build_cache_raw.get("reclaimable_bytes"), "build_cache.reclaimable_bytes"),
        "max_bytes": _int(build_cache_raw.get("max_bytes"), "build_cache.max_bytes"),
    }
    if build_cache["reclaimable_bytes"] > build_cache["bytes"]:
        raise ValueError("build_cache.reclaimable_bytes cannot exceed build_cache.bytes")

    return {
        "schema": OUTPUT_SCHEMA,
        "now_epoch": now_epoch,
        "retention_seconds": retention_seconds,
        "superseded_keep_per_lineage": reserve,
        "root_used_percent": root_used,
        "disk_high_watermark_percent": high_watermark,
        "images": sorted(images.values(), key=lambda item: item["id"]),
        "services": sorted(services, key=lambda item: (item["project"], item["service"])),
        "volumes": sorted(volumes, key=lambda item: item["name"]),
        "build_cache": build_cache,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args()
    try:
        payload = json.load(sys.stdin)
        if not isinstance(payload, dict):
            raise ValueError("input must be a JSON object")
        json.dump(build_inventory(payload), sys.stdout, sort_keys=True, separators=(",", ":"))
        sys.stdout.write("\n")
        return 0
    except (ValueError, json.JSONDecodeError) as exc:
        print(f"inventory error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
