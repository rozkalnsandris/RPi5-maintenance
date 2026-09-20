#!/usr/bin/env python3
"""Deterministic, read-only observability evidence classifier.

The classifier consumes sanitized evidence. It never invokes systemd, journalctl,
Hermes, Docker, or any other runtime command, and it has no remediation path.
"""

from __future__ import annotations

import argparse
from collections import Counter
import json
import re
import sys
from typing import Any

INPUT_SCHEMA = "rpi5-observability-evidence.v1"
OUTPUT_SCHEMA = "rpi5-observability-classification.v1"

AUTH_PATTERNS = (
    re.compile(r"invalid refresh token", re.I),
    re.compile(r"persisted session invalid", re.I),
    re.compile(r"device authorization flow", re.I),
    re.compile(r"no valid session", re.I),
    re.compile(r"pending[- ]auth", re.I),
    re.compile(r"pairing required", re.I),
)
READY_PATTERNS = (
    re.compile(r"session restored", re.I),
    re.compile(r"channel subscribed", re.I),
    re.compile(r"device ready", re.I),
    re.compile(r"readiness.*pass", re.I),
)
V8_OOM_PATTERNS = (
    re.compile(r"javascript heap out of memory", re.I),
    re.compile(r"ineffective mark-compacts", re.I),
    re.compile(r"allocation failed.*heap", re.I),
)
PYTHON_OOM_PATTERNS = (
    re.compile(r"\bmemoryerror\b", re.I),
    re.compile(r"cannot allocate memory", re.I),
)


def _require_int(value: Any, context: str, *, minimum: int = 0) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value < minimum:
        raise ValueError(f"{context} must be an integer >= {minimum}")
    return value


def _strings(value: Any, context: str) -> list[str]:
    if value is None:
        return []
    if not isinstance(value, list) or any(not isinstance(item, str) for item in value):
        raise ValueError(f"{context} must be an array of strings")
    return value


def _matches(lines: list[str], patterns: tuple[re.Pattern[str], ...]) -> list[str]:
    return sorted({line for line in lines if any(pattern.search(line) for pattern in patterns)})


def _service_key(raw: dict[str, Any], index: int) -> tuple[str, str, str]:
    manager = raw.get("manager")
    unit = raw.get("unit")
    if manager not in {"system", "user"}:
        raise ValueError(f"services[{index}].manager must be system or user")
    if not isinstance(unit, str) or not unit:
        raise ValueError(f"services[{index}].unit must be a non-empty string")
    return manager, unit, f"{manager}:{unit}"


def _classify_service(raw: dict[str, Any], index: int, loop_threshold: int) -> dict[str, Any]:
    manager, unit, key = _service_key(raw, index)
    active = raw.get("active_state")
    sub = raw.get("sub_state")
    result = raw.get("result")
    if not all(isinstance(value, str) and value for value in (active, sub, result)):
        raise ValueError(f"services[{index}] active_state, sub_state and result must be non-empty strings")

    restarts = _require_int(raw.get("restart_count", 0), f"services[{index}].restart_count")
    activations = _require_int(raw.get("activation_count", 0), f"services[{index}].activation_count")
    events = _strings(raw.get("evidence", []), f"services[{index}].evidence")
    auth_evidence = _matches(events, AUTH_PATTERNS)
    ready_evidence = _matches(events, READY_PATTERNS)

    first_failure = raw.get("first_failure_epoch")
    last_failure = raw.get("last_failure_epoch")
    for name, value in (("first_failure_epoch", first_failure), ("last_failure_epoch", last_failure)):
        if value is not None:
            _require_int(value, f"services[{index}].{name}", minimum=1)

    timer_unit = raw.get("timer_unit")
    if timer_unit is not None and (not isinstance(timer_unit, str) or not timer_unit):
        raise ValueError(f"services[{index}].timer_unit must be null or a non-empty string")

    intentional_fail_closed = raw.get("intentional_fail_closed", False)
    readiness_required = raw.get("readiness_required", False)
    if not isinstance(intentional_fail_closed, bool):
        raise ValueError(f"services[{index}].intentional_fail_closed must be boolean")
    if not isinstance(readiness_required, bool):
        raise ValueError(f"services[{index}].readiness_required must be boolean")

    root_causes: list[str] = []
    state = "ready"
    recovered = False

    if auth_evidence:
        state = "authorization-required"
        root_causes.append("service.authorization-required")
    elif intentional_fail_closed and (active == "failed" or result != "success"):
        state = "intentional-fail-closed"
        root_causes.append("service.intentional-fail-closed")
    elif active == "failed" or result != "success":
        state = "persistent-failure"
        root_causes.append("service.persistent-failure")
    elif restarts >= loop_threshold or activations >= loop_threshold:
        state = "failure-loop"
        root_causes.append("service.failure-loop")
    elif active != "active":
        state = "inactive"
        root_causes.append("service.inactive")
    elif readiness_required and not ready_evidence:
        state = "active-not-ready"
        root_causes.append("service.active-not-ready")
    elif last_failure is not None and ready_evidence:
        state = "recovered-transient"
        recovered = True
        root_causes.append("service.recovered-transient")
    elif last_failure is not None:
        state = "historical-stale-failure"
        root_causes.append("service.historical-stale-failure")

    return {
        "key": key,
        "manager": manager,
        "unit": unit,
        "state": state,
        "root_causes": root_causes,
        "active_state": active,
        "sub_state": sub,
        "result": result,
        "restart_count": restarts,
        "activation_count": activations,
        "timer_unit": timer_unit,
        "first_failure_epoch": first_failure,
        "last_failure_epoch": last_failure,
        "authorization_evidence": auth_evidence,
        "readiness_evidence": ready_evidence,
        "readiness_required": readiness_required,
        "intentional_fail_closed": intentional_fail_closed,
        "recovered": recovered,
    }


def _classify_memory(raw: Any) -> list[dict[str, Any]]:
    if raw is None:
        return []
    if not isinstance(raw, dict):
        raise ValueError("memory must be an object")

    findings: list[dict[str, Any]] = []
    kernel = _strings(raw.get("kernel_events", []), "memory.kernel_events")
    cgroups = raw.get("cgroups", [])
    user = _strings(raw.get("user_space_events", []), "memory.user_space_events")

    for line in kernel:
        if re.search(r"out of memory|oom-kill|killed process", line, re.I):
            findings.append({"class": "kernel-oom", "root_cause": "memory.kernel-oom", "evidence": line})

    if not isinstance(cgroups, list):
        raise ValueError("memory.cgroups must be an array")
    for index, item in enumerate(cgroups):
        if not isinstance(item, dict):
            raise ValueError(f"memory.cgroups[{index}] must be an object")
        unit = item.get("unit")
        if not isinstance(unit, str) or not unit:
            raise ValueError(f"memory.cgroups[{index}].unit must be a non-empty string")
        oom = _require_int(item.get("oom", 0), f"memory.cgroups[{index}].oom")
        oom_kill = _require_int(item.get("oom_kill", 0), f"memory.cgroups[{index}].oom_kill")
        result = item.get("result", "success")
        if not isinstance(result, str) or not result:
            raise ValueError(f"memory.cgroups[{index}].result must be a non-empty string")
        if oom or oom_kill or result == "oom-kill":
            findings.append(
                {
                    "class": "cgroup-oom",
                    "root_cause": "memory.cgroup-oom",
                    "unit": unit,
                    "oom": oom,
                    "oom_kill": oom_kill,
                    "result": result,
                }
            )

    for line in user:
        if any(pattern.search(line) for pattern in V8_OOM_PATTERNS):
            findings.append({"class": "user-space-v8-oom", "root_cause": "memory.user-space-v8-oom", "evidence": line})
        elif any(pattern.search(line) for pattern in PYTHON_OOM_PATTERNS):
            findings.append({"class": "user-space-runtime-oom", "root_cause": "memory.user-space-runtime-oom", "evidence": line})

    return findings


def _classify_hermes(raw: Any, now_epoch: int, late_threshold: int) -> dict[str, Any] | None:
    if raw is None:
        return None
    if not isinstance(raw, dict):
        raise ValueError("hermes must be an object")

    doctor_ok = raw.get("doctor_ok")
    if not isinstance(doctor_ok, bool):
        raise ValueError("hermes.doctor_ok must be boolean")
    next_run_at = raw.get("next_run_at")
    if next_run_at is not None:
        _require_int(next_run_at, "hermes.next_run_at", minimum=1)

    executions = raw.get("executions", [])
    if not isinstance(executions, list):
        raise ValueError("hermes.executions must be an array")

    findings: list[dict[str, Any]] = []
    state_counts: Counter[str] = Counter()
    delivery_counts: Counter[str] = Counter()

    for index, item in enumerate(executions):
        if not isinstance(item, dict):
            raise ValueError(f"hermes.executions[{index}] must be an object")
        state = item.get("state")
        delivery = item.get("delivery_state", "not-applicable")
        if not isinstance(state, str) or not state:
            raise ValueError(f"hermes.executions[{index}].state must be a non-empty string")
        if not isinstance(delivery, str) or not delivery:
            raise ValueError(f"hermes.executions[{index}].delivery_state must be a non-empty string")
        state_counts[state] += 1
        delivery_counts[delivery] += 1

        if state in {"failed", "error"}:
            findings.append({"class": "execution-failure", "root_cause": "hermes.execution-failure", "index": index})
        elif state == "unknown":
            findings.append({"class": "unknown-attempt", "root_cause": "hermes.unknown-attempt", "index": index})
        elif state in {"missed", "late", "catch-up"}:
            findings.append({"class": f"{state}-dispatch", "root_cause": f"hermes.{state}-dispatch", "index": index})

        if delivery in {"failed", "error"}:
            findings.append({"class": "delivery-failure", "root_cause": "hermes.delivery-failure", "index": index})

    if not doctor_ok:
        findings.append({"class": "doctor-failure", "root_cause": "hermes.doctor-failure"})
    if next_run_at is not None and next_run_at + late_threshold < now_epoch:
        findings.append(
            {
                "class": "parked-next-run",
                "root_cause": "hermes.parked-next-run",
                "next_run_at": next_run_at,
                "age_seconds": now_epoch - next_run_at,
            }
        )

    return {
        "doctor_ok": doctor_ok,
        "next_run_at": next_run_at,
        "state_counts": dict(sorted(state_counts.items())),
        "delivery_counts": dict(sorted(delivery_counts.items())),
        "findings": findings,
    }


def classify(payload: dict[str, Any]) -> dict[str, Any]:
    if payload.get("schema") != INPUT_SCHEMA:
        raise ValueError(f"schema must be {INPUT_SCHEMA}")
    now_epoch = _require_int(payload.get("now_epoch"), "now_epoch", minimum=1)
    loop_threshold = _require_int(payload.get("loop_threshold", 3), "loop_threshold", minimum=2)
    hermes_late_threshold = _require_int(
        payload.get("hermes_late_threshold_seconds", 3600),
        "hermes_late_threshold_seconds",
        minimum=1,
    )

    services_raw = payload.get("services", [])
    if not isinstance(services_raw, list):
        raise ValueError("services must be an array")
    services: list[dict[str, Any]] = []
    for index, item in enumerate(services_raw):
        if not isinstance(item, dict):
            raise ValueError(f"services[{index}] must be an object")
        services.append(_classify_service(item, index, loop_threshold))

    memory = _classify_memory(payload.get("memory"))
    hermes = _classify_hermes(payload.get("hermes"), now_epoch, hermes_late_threshold)

    root_causes = sorted(
        {
            cause
            for service in services
            for cause in service["root_causes"]
        }
        | {item["root_cause"] for item in memory}
        | ({item["root_cause"] for item in hermes["findings"]} if hermes else set())
    )

    summary = {
        "service_counts": dict(sorted(Counter(item["state"] for item in services).items())),
        "memory_findings": len(memory),
        "hermes_findings": 0 if hermes is None else len(hermes["findings"]),
        "root_cause_count": len(root_causes),
    }

    return {
        "schema": OUTPUT_SCHEMA,
        "now_epoch": now_epoch,
        "services": services,
        "memory": memory,
        "hermes": hermes,
        "root_causes": root_causes,
        "summary": summary,
        "safety": {
            "read_only_classifier": True,
            "remediation_authorized": False,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "input",
        nargs="?",
        default="-",
        help="sanitized JSON evidence file, or - for stdin",
    )
    args = parser.parse_args()

    try:
        if args.input == "-":
            payload = json.load(sys.stdin)
        else:
            with open(args.input, "r", encoding="utf-8") as handle:
                payload = json.load(handle)
        if not isinstance(payload, dict):
            raise ValueError("top-level input must be an object")
        result = classify(payload)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    json.dump(result, sys.stdout, sort_keys=True, indent=2)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
