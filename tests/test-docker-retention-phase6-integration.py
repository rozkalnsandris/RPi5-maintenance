#!/usr/bin/env python3
from pathlib import Path
import re
import subprocess

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
assert "RETENTION_CV_PROJECT_NAME" in wrapper
assert "RETENTION_CV_COMPOSE_FILES" in wrapper
assert "parse_cv_compose_files" in wrapper
assert '--compose-project-name "cv=${RETENTION_CV_PROJECT_NAME}"' in wrapper
assert '"${cv_compose_args[@]}"' in wrapper
assert "read-only retention evidence complete" in wrapper

# Exercise the exact parser function embedded in the production wrapper without
# running the privileged wrapper itself. This catches the 2026-09-27 regression
# where the reviewed comma-separated config value was treated as one run ID.
parser_match = re.search(
    r"(?ms)^parse_trusted_evidence_runs\(\) \{\n.*?^\}\n",
    wrapper,
)
assert parser_match is not None
parser_source = parser_match.group(0)


def parse_trusted_runs(raw: str) -> subprocess.CompletedProcess[str]:
    script = (
        "set -Eeuo pipefail\n"
        + parser_source
        + "\ntrusted_args=()\n"
        + 'parse_trusted_evidence_runs "$1" trusted_args\n'
        + 'printf "%s\\n" "${trusted_args[@]}"\n'
    )
    return subprocess.run(
        ["bash", "-c", script, "_", raw],
        check=False,
        text=True,
        capture_output=True,
    )


two_runs = parse_trusted_runs("20260913_022000,20260920_022000")
assert two_runs.returncode == 0, two_runs.stderr
assert two_runs.stdout.splitlines() == [
    "--trusted-evidence-run",
    "20260913_022000",
    "--trusted-evidence-run",
    "20260920_022000",
]

single_run = parse_trusted_runs("20260920_022000")
assert single_run.returncode == 0, single_run.stderr
assert single_run.stdout.splitlines() == [
    "--trusted-evidence-run",
    "20260920_022000",
]

for malformed in (
    "",
    "20260920_022000,",
    ",20260920_022000",
    "20260913_022000,,20260920_022000",
    "20260913_022000 20260920_022000",
    "2026091_022000",
    "not-a-run-id",
):
    result = parse_trusted_runs(malformed)
    assert result.returncode != 0, malformed

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
assert "RETENTION_CV_PROJECT_NAME=" in config
assert "RETENTION_CV_COMPOSE_FILES=" in config
assert "RETENTION_TRUSTED_EVIDENCE_RUNS=" in config
assert "RETENTION_BUILD_CACHE_MAX_BYTES=8589934592" in config
assert "RETENTION_SUPERSEDED_KEEP_PER_LINEAGE=1" in config

# Existing systemd schedule continues to call the canonical installed path,
# which becomes the reviewed Phase 6 wrapper only after separately authorized
# LIVE refresh.
assert "ExecStart=/usr/local/sbin/rpi5-update" in service

print("Phase 6 staged Docker retention integration source contract: PASS")
