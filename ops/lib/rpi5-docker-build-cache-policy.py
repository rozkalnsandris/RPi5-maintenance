#!/usr/bin/env python3
"""Pure policy for storage-bounded Docker BuildKit cache pruning.

This module never invokes Docker and never mutates cache. It consumes an existing
RPi5 Docker retention planner result and emits a deterministic future prune plan.
"""
from __future__ import annotations

import re
from typing import Any

INPUT_SCHEMA = "rpi5-docker-retention-plan-result.v1"
OUTPUT_SCHEMA = "rpi5-docker-build-cache-plan.v1"
BUILDER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")


class CachePolicyError(ValueError):
    pass


def _uint(value: Any, context: str, *, positive: bool = False) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        raise CachePolicyError(f"{context} must be a non-negative integer")
    if positive and value == 0:
        raise CachePolicyError(f"{context} must be positive")
    return value


def _builder(value: Any) -> str:
    if not isinstance(value, str) or not BUILDER_RE.fullmatch(value):
        raise CachePolicyError(f"invalid builder identity: {value!r}")
    return value


def future_prune_argv(builder: str, min_age_seconds: int, max_used_space_bytes: int) -> list[str]:
    builder = _builder(builder)
    min_age_seconds = _uint(min_age_seconds, "min_age_seconds", positive=True)
    max_used_space_bytes = _uint(max_used_space_bytes, "max_used_space_bytes", positive=True)
    return [
        "docker",
        "buildx",
        "--builder",
        builder,
        "prune",
        "--force",
        "--filter",
        f"until={min_age_seconds}s",
        "--filter",
        "inuse=false",
        "--filter",
        "shared=false",
        "--max-used-space",
        f"{max_used_space_bytes}B",
    ]


def build_cache_plan(retention_plan: dict[str, Any], *, builder: str, min_age_seconds: int) -> dict[str, Any]:
    if not isinstance(retention_plan, dict) or retention_plan.get("schema") != INPUT_SCHEMA:
        raise CachePolicyError(f"retention plan schema must be {INPUT_SCHEMA}")
    builder = _builder(builder)
    min_age_seconds = _uint(min_age_seconds, "min_age_seconds", positive=True)

    cache = retention_plan.get("build_cache")
    if not isinstance(cache, dict):
        raise CachePolicyError("retention plan build_cache must be an object")
    used = _uint(cache.get("bytes"), "build_cache.bytes")
    reclaimable = _uint(cache.get("reclaimable_bytes"), "build_cache.reclaimable_bytes")
    maximum = _uint(cache.get("max_bytes"), "build_cache.max_bytes", positive=True)
    if reclaimable > used:
        raise CachePolicyError("build_cache.reclaimable_bytes cannot exceed build_cache.bytes")
    expected_exceeded = used > maximum
    if cache.get("exceeded") is not expected_exceeded:
        raise CachePolicyError("build_cache.exceeded contradicts bytes/max_bytes")
    if cache.get("action") != "report-only":
        raise CachePolicyError("build_cache.action must remain report-only before Phase 5 planning")

    excess = max(0, used - maximum)
    result: dict[str, Any] = {
        "schema": OUTPUT_SCHEMA,
        "builder": builder,
        "policy": {
            "min_age_seconds": min_age_seconds,
            "max_used_space_bytes": maximum,
            "filters": [f"until={min_age_seconds}s", "inuse=false", "shared=false"],
            "include_internal_frontend": False,
        },
        "evidence": {
            "used_bytes": used,
            "reclaimable_bytes": reclaimable,
            "excess_bytes": excess,
        },
        "required_capabilities": [
            "docker-buildx",
            "explicit-builder",
            "prune-filter",
            "max-used-space",
        ],
        "action": "noop",
        "reason": "within-max-used-space",
        "future_prune_argv": None,
    }

    if not expected_exceeded:
        return result

    if reclaimable == 0:
        result["action"] = "blocked"
        result["reason"] = "no-reclaimable-cache-evidence"
        return result
    if reclaimable < excess:
        result["action"] = "blocked"
        result["reason"] = "insufficient-reclaimable-cache-evidence"
        return result

    result["action"] = "prune-required"
    result["reason"] = "max-used-space-exceeded"
    result["future_prune_argv"] = future_prune_argv(builder, min_age_seconds, maximum)
    return result
