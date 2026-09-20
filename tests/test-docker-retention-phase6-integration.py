#!/usr/bin/env python3
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
WRAPPER = ROOT / "ops/bin/rpi5-update-scheduled"
CORE = ROOT / "ops/bin/rpi5-update"
REFRESH = ROOT / "ops/bin/rpi5-maintenance-retention-refresh"
CONFIG = ROOT / "ops/config/docker-retention.conf"
SERVICE = ROOT / "ops/systemd/rpi5-update.service"

wrapper = WRAPPER.read_text(encoding="utf-8")
core = CORE.read_text(encoding="utf-8")
refresh = REFRESH.read_text(encoding="utf-8")
config = CONFIG.read_text(encoding="utf-8")
service = SERVICE.read_text(encoding="utf-8")

assert re.search(r"^[ \t]*docker[ \t]+builder[ \t]+prune\b", wrapper, re.MULTILINE) is None
assert re.search(r"^[ \t]*docker[ \t]+buildx[ \t]+prune\b", wrapper, re.MULTILINE) is None
assert "--apply" not in wrapper
assert "docker image prune -f --filter" in wrapper
assert "export DOCKER_CLEANUP=no" in wrapper
assert "rpi5-update-v28-core" in wrapper
assert "rpi5-docker-retention-report" in wrapper
assert "rpi5-docker-retention-executor" in wrapper
assert "rpi5-docker-build-cache-plan" in wrapper
assert "RETENTION_MODE" in wrapper and "off|report" in wrapper
assert "RETENTION_TRUSTED_EVIDENCE_RUNS" in wrapper
assert "read-only retention evidence complete" in wrapper

# The extracted core intentionally retains the historical implementation so
# the Phase 6 change is a wrapper/integration boundary, not a V28 rewrite.
assert "docker builder prune" in core
assert "-a" in core
assert "Versija: 28" in core

assert "rpi5-update.timer" in refresh
assert "systemctl is-active --quiet rpi5-update.timer" in refresh
assert "systemctl restart" not in refresh
assert "systemctl start" not in refresh
assert "systemctl daemon-reload" not in refresh
assert "docker image prune" not in refresh
assert "docker builder prune" not in refresh
assert "docker buildx prune" not in refresh
assert "RETENTION_CONFIG" in refresh
assert "installed V28 core identity mismatch" in refresh

assert "RETENTION_MODE=off" in config
assert "RETENTION_TRUSTED_EVIDENCE_RUNS=" in config
assert "RETENTION_BUILD_CACHE_MAX_BYTES=8589934592" in config
assert "RETENTION_SUPERSEDED_KEEP_PER_LINEAGE=1" in config

# Existing systemd schedule continues to call the canonical installed path,
# which becomes the reviewed Phase 6 wrapper only after separately authorized
# LIVE refresh.
assert "ExecStart=/usr/local/sbin/rpi5-update" in service

print("Phase 6 staged Docker retention integration source contract: PASS")
