#!/usr/bin/env python3
"""Pure Docker image-retention planner.

This module never invokes Docker and never deletes anything. It accepts a
sanitized runtime inventory and emits deterministic dry-run decisions for a
later, separately reviewed executor.
"""

from __future__ import annotations

import argparse
from collections import Counter
import json
import re
import sys
from typing import Any

IMAGE_ID_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
INPUT_SCHEMA = "rpi5-docker-retention-plan.v1"
OUTPUT_SCHEMA = "rpi5-docker-retention-plan-result.v1"


def _require_int(payload: dict[str, Any], key: str) -> int:
    value = payload.get(key)
    if not isinstance(value, int) or isinstance(value, bool):
        raise ValueError(f"{key} must be an integer")
    return value


def _require_image_id(value: Any, context: str) -> str:
    if not isinstance(value, str) or not IMAGE_ID_RE.fullmatch(value):
        raise ValueError(f"invalid image id for {context}: {value!r}")
    return value


def _string_list(value: Any, context: str) -> list[str]:
    if not isinstance(value, list) or any(not isinstance(item, str) or not item for item in value):
        raise ValueError(f"{context} must be a list of non-empty strings")
    return sorted(set(value))


def build_plan(payload: dict[str, Any]) -> dict[str, Any]:
    if payload.get("schema") != INPUT_SCHEMA:
        raise ValueError(f"schema must be {INPUT_SCHEMA}")

    now_epoch = _require_int(payload, "now_epoch")
    retention_seconds = _require_int(payload, "retention_seconds")
    reserve_count = _require_int(payload, "superseded_keep_per_lineage")
    root_used_percent = _require_int(payload, "root_used_percent")
    high_watermark_percent = _require_int(payload, "disk_high_watermark_percent")

    if now_epoch <= 0:
        raise ValueError("now_epoch must be positive")
    if retention_seconds < 0 or reserve_count < 0:
        raise ValueError("retention_seconds and superseded_keep_per_lineage must be non-negative")
    if not 0 <= root_used_percent <= 100:
        raise ValueError("root_used_percent must be between 0 and 100")
    if not 1 <= high_watermark_percent <= 100:
        raise ValueError("disk_high_watermark_percent must be between 1 and 100")

    images_raw = payload.get("images")
    services_raw = payload.get("services")
    volumes_raw = payload.get("volumes", [])
    cache_raw = payload.get("build_cache")
    if not isinstance(images_raw, list) or not isinstance(services_raw, list):
        raise ValueError("images and services must be arrays")
    if not isinstance(volumes_raw, list):
        raise ValueError("volumes must be an array")
    if not isinstance(cache_raw, dict):
        raise ValueError("build_cache must be an object")

    images: dict[str, dict[str, Any]] = {}
    for index, raw in enumerate(images_raw):
        if not isinstance(raw, dict):
            raise ValueError(f"images[{index}] must be an object")
        image_id = _require_image_id(raw.get("id"), f"images[{index}]")
        if image_id in images:
            raise ValueError(f"duplicate image id: {image_id}")
        created_epoch = raw.get("created_epoch")
        size_bytes = raw.get("size_bytes")
        if not isinstance(created_epoch, int) or isinstance(created_epoch, bool) or created_epoch < 0:
            raise ValueError(f"invalid created_epoch for {image_id}")
        if not isinstance(size_bytes, int) or isinstance(size_bytes, bool) or size_bytes < 0:
            raise ValueError(f"invalid size_bytes for {image_id}")
        images[image_id] = {
            "id": image_id,
            "created_epoch": created_epoch,
            "size_bytes": size_bytes,
            "repositories": _string_list(raw.get("repositories", []), f"repositories for {image_id}"),
            "container_refs": _string_list(raw.get("container_refs", []), f"container_refs for {image_id}"),
        }

    service_keys: set[str] = set()
    lineage_to_services: dict[str, list[str]] = {}
    protected_roles: dict[str, set[str]] = {}
    blocked_lineages: dict[str, list[str]] = {}
    services: list[dict[str, Any]] = []

    for index, raw in enumerate(services_raw):
        if not isinstance(raw, dict):
            raise ValueError(f"services[{index}] must be an object")
        project = raw.get("project")
        service = raw.get("service")
        lineage = raw.get("lineage")
        if not all(isinstance(value, str) and value for value in (project, service, lineage)):
            raise ValueError(f"invalid service identity at services[{index}]")
        key = f"{project}/{service}"
        if key in service_keys:
            raise ValueError(f"duplicate service identity: {key}")
        service_keys.add(key)

        current_id = _require_image_id(raw.get("current_id"), f"current_id for {key}")
        candidate_ids = [_require_image_id(item, f"candidate_ids for {key}") for item in raw.get("candidate_ids", [])]
        previous_ids = [_require_image_id(item, f"previous_known_good_ids for {key}") for item in raw.get("previous_known_good_ids", [])]
        candidate_ids = sorted(set(candidate_ids))
        previous_ids = sorted(set(previous_ids))

        all_ids = [current_id, *candidate_ids, *previous_ids]
        for image_id in all_ids:
            if image_id not in images:
                raise ValueError(f"unknown protected image for {key}: {image_id}")
            if lineage not in images[image_id]["repositories"]:
                raise ValueError(f"protected image outside lineage for {key}: {image_id}")
        if not images[current_id]["container_refs"]:
            raise ValueError(f"current image is not container-referenced for {key}: {current_id}")
        if current_id in previous_ids:
            raise ValueError(f"current image cannot also be previous-known-good for {key}")
        if set(candidate_ids) & set(previous_ids):
            raise ValueError(f"candidate and previous-known-good overlap for {key}")

        lineage_to_services.setdefault(lineage, []).append(key)
        protected_roles.setdefault(current_id, set()).add("current")
        for image_id in candidate_ids:
            protected_roles.setdefault(image_id, set()).add("candidate")
        for image_id in previous_ids:
            protected_roles.setdefault(image_id, set()).add("previous-known-good")
        if not previous_ids:
            blocked_lineages.setdefault(lineage, []).append("missing-previous-known-good")

        services.append(
            {
                "key": key,
                "project": project,
                "service": service,
                "lineage": lineage,
                "current_id": current_id,
                "candidate_ids": candidate_ids,
                "previous_known_good_ids": previous_ids,
            }
        )

    for lineage, owners in lineage_to_services.items():
        if len(owners) > 1:
            blocked_lineages.setdefault(lineage, []).append("shared-lineage-across-services")

    managed_lineages = set(lineage_to_services)
    pending_by_lineage: dict[str, list[str]] = {lineage: [] for lineage in managed_lineages}
    decisions: dict[str, dict[str, Any]] = {}

    for image_id, image in images.items():
        matching = sorted(managed_lineages.intersection(image["repositories"]))
        reasons: list[str] = []

        if image["container_refs"]:
            action, role = "protect", "container-referenced"
            reasons.append("referenced-by-container")
        elif image_id in protected_roles:
            action, role = "protect", "+".join(sorted(protected_roles[image_id]))
            reasons.append("protected-identity")
        elif not image["repositories"]:
            action, role = "ignore", "dangling"
            reasons.append("handled-by-existing-dangling-policy")
        elif not matching:
            action, role = "ignore", "unmanaged"
            reasons.append("outside-managed-lineages")
        elif len(matching) > 1:
            action, role = "block", "ambiguous"
            reasons.append("multiple-managed-lineages")
        else:
            lineage = matching[0]
            if lineage in blocked_lineages:
                action, role = "block", "ambiguous"
                reasons.extend(sorted(set(blocked_lineages[lineage])))
            elif now_epoch - image["created_epoch"] < retention_seconds:
                action, role = "protect", "young"
                reasons.append("younger-than-retention")
            else:
                action, role = "pending", "superseded"
                reasons.append("eligible-by-age")
                pending_by_lineage[lineage].append(image_id)

        decisions[image_id] = {
            "id": image_id,
            "action": action,
            "role": role,
            "reasons": reasons,
            "lineages": matching,
            "created_epoch": image["created_epoch"],
            "size_bytes": image["size_bytes"],
            "repositories": image["repositories"],
            "container_refs": image["container_refs"],
        }

    for lineage, image_ids in pending_by_lineage.items():
        image_ids.sort(key=lambda item: (images[item]["created_epoch"], item), reverse=True)
        for position, image_id in enumerate(image_ids):
            decision = decisions[image_id]
            if position < reserve_count:
                decision["action"] = "protect"
                decision["role"] = "count-reserve"
                decision["reasons"].append("newest-superseded-reserve")
            else:
                decision["action"] = "delete"
                decision["role"] = "superseded"
                decision["reasons"].append("beyond-count-reserve")

    volumes: list[dict[str, Any]] = []
    volume_counts = Counter()
    for index, raw in enumerate(volumes_raw):
        if not isinstance(raw, dict):
            raise ValueError(f"volumes[{index}] must be an object")
        name = raw.get("name")
        project = raw.get("project")
        kind = raw.get("kind")
        if not isinstance(name, str) or not name:
            raise ValueError(f"invalid volume name at volumes[{index}]")
        if project is not None and (not isinstance(project, str) or not project):
            raise ValueError(f"invalid volume project at volumes[{index}]")
        if kind not in {"named", "anonymous"}:
            raise ValueError(f"volume kind must be named or anonymous for {name}")
        volume_counts[kind] += 1
        volumes.append({"name": name, "project": project, "kind": kind, "action": "report-only"})

    cache_bytes = cache_raw.get("bytes")
    reclaimable_bytes = cache_raw.get("reclaimable_bytes")
    max_bytes = cache_raw.get("max_bytes")
    for key, value in (("bytes", cache_bytes), ("reclaimable_bytes", reclaimable_bytes), ("max_bytes", max_bytes)):
        if not isinstance(value, int) or isinstance(value, bool) or value < 0:
            raise ValueError(f"build_cache.{key} must be a non-negative integer")
    if reclaimable_bytes > cache_bytes:
        raise ValueError("build_cache.reclaimable_bytes cannot exceed build_cache.bytes")

    action_counts = Counter(decision["action"] for decision in decisions.values())
    delete_ids = sorted(image_id for image_id, decision in decisions.items() if decision["action"] == "delete")
    delete_bytes = sum(images[image_id]["size_bytes"] for image_id in delete_ids)

    return {
        "schema": OUTPUT_SCHEMA,
        "watermark": {
            "root_used_percent": root_used_percent,
            "high_percent": high_watermark_percent,
            "exceeded": root_used_percent >= high_watermark_percent,
        },
        "build_cache": {
            "bytes": cache_bytes,
            "reclaimable_bytes": reclaimable_bytes,
            "max_bytes": max_bytes,
            "exceeded": cache_bytes > max_bytes,
            "action": "report-only",
        },
        "summary": {
            "images": len(decisions),
            "delete": action_counts["delete"],
            "delete_bytes": delete_bytes,
            "protect": action_counts["protect"],
            "block": action_counts["block"],
            "ignore": action_counts["ignore"],
            "named_volumes": volume_counts["named"],
            "anonymous_volumes": volume_counts["anonymous"],
        },
        "blocked_lineages": {
            lineage: sorted(set(reasons)) for lineage, reasons in sorted(blocked_lineages.items())
        },
        "services": sorted(services, key=lambda item: item["key"]),
        "images": [decisions[image_id] for image_id in sorted(decisions)],
        "delete_ids": delete_ids,
        "volumes": sorted(volumes, key=lambda item: item["name"]),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("inventory", nargs="?", default="-", help="JSON inventory path, or - for stdin")
    parser.add_argument("--pretty", action="store_true", help="pretty-print result JSON")
    args = parser.parse_args()

    try:
        if args.inventory == "-":
            payload = json.load(sys.stdin)
        else:
            with open(args.inventory, "r", encoding="utf-8") as handle:
                payload = json.load(handle)
        result = build_plan(payload)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"retention-plan error: {exc}", file=sys.stderr)
        return 2

    json.dump(result, sys.stdout, sort_keys=True, indent=2 if args.pretty else None)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
