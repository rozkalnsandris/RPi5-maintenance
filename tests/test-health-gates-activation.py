#!/usr/bin/env python3
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OPERATOR = ROOT / "ops/bin/rpi5-health-gates-activate"
text = OPERATOR.read_text(encoding="utf-8")

expected_pairs = [
    ("ops/lib/rpi5-service-health.sh", "/usr/local/lib/rpi5-maintenance/rpi5-service-health.sh"),
    ("ops/config/service-health.tsv", "/etc/rpi5-maintenance/service-health.tsv"),
    ("ops/lib/rpi5-update-compose-health.sh", "/usr/local/lib/rpi5-maintenance/rpi5-update-compose-health.sh"),
    ("ops/bin/rpi5-post-reboot", "/usr/local/sbin/rpi5-post-reboot"),
    ("ops/bin/rpi5-monitor", "/usr/local/sbin/rpi5-monitor"),
    ("ops/systemd/rpi5-monitor.service", "/etc/systemd/system/rpi5-monitor.service"),
]

source_block = re.search(r"readonly -a SOURCE_REL=\((.*?)\n\)", text, re.S)
dest_block = re.search(r"readonly -a DEST=\((.*?)\n\)", text, re.S)
mode_block = re.search(r"readonly -a MODE=\((.*?)\)", text, re.S)
assert source_block and dest_block and mode_block
sources = re.findall(r"'([^']+)'", source_block.group(1))
dests = re.findall(r"'([^']+)'", dest_block.group(1))
modes = mode_block.group(1).split()
assert list(zip(sources, dests, strict=True)) == expected_pairs
assert modes == ["0644", "0644", "0644", "0750", "0750", "0644"]

required_markers = [
    "--source-sha",
    "git ls-remote",
    "EXACT_MAIN_VALIDATE=PASS",
    "head_sha",
    "event': 'push'",
    "conclusion') == 'success'",
    "EXPECTED_HOST='rpi5'",
    "EXPECTED_PRE_MONITOR_SHA256='d16af598d02738cf9a4c11646577cea21e88c96d447e7566204fae37b1362166'",
    "EXPECTED_PRE_POST_REBOOT_SHA256='ef59cb17ec1d8eae39aad4d503837444cd0bfdada5d3dd572bd1f6e44c230ada'",
    "EXPECTED_PRE_COMPOSE_HEALTH_SHA256='36778bc5f36232d24f3c629a092b829b4e695a602c056ce01d9b62fda3e07814'",
    "EXPECTED_PRE_MONITOR_SERVICE_SHA256='9af367a737eb0c148549c77ee79d87f2b16e4779817d50560af0e8d5c5502228'",
    "assert_live_matches_source 'ops/lib/rpi5-maintenance-health.sh'",
    "assert_live_matches_source 'ops/bin/rpi5-update'",
    "assert_live_matches_source 'ops/systemd/rpi5-monitor.timer'",
    "rpi5-monitor.timer is not active",
    "rpi5-update.timer is not active",
    "[[ ! -e /run/reboot-required ]]",
    "/run/lock/rpi5-update.lock",
    "/run/lock/rpi5-backup.lock",
    "/run/lock/rpi5-maintenance-exclusive.lock",
    "validate_lock_path",
    "verify_lock_availability",
    "create_lock_file_if_missing",
    "os.O_RDWR | os.O_CREAT | os.O_EXCL",
    "os.O_NOFOLLOW",
    "MUTATION_SCOPE=6-files plus-missing-lockfiles",
    "systemctl daemon-reload",
    "/usr/local/sbin/rpi5-monitor",
    "no automatic retry, rollback, cleanup, restart, or reboot",
    "ROLLBACK=not-automatic",
    "REBOOT_REQUIRED=no",
]
for marker in required_markers:
    assert marker in text, marker

assert 'unsafe/missing lock file:' not in text
assert '[[ -e "$path" ]] || return 0' in text

create_lock_block = re.search(r"create_lock_file_if_missing\(\) \{(.*?)\n\}", text, re.S)
assert create_lock_block
block = create_lock_block.group(1)
assert block.index("MUTATION_STARTED=true") < block.index("python3 - \"$path\"")
assert block.index("os.O_RDWR | os.O_CREAT | os.O_EXCL") < block.index("os.open(path, flags, 0o600)")
assert block.index("raise SystemExit(17)") < block.index("require_root_file")

preflight = text.index("if [[ \"$ACTION\" == '--preflight' ]]; then")
initial_baseline = text.rindex("verify_runtime_baseline", 0, preflight)
lock_probe = text.rindex("verify_lock_availability", 0, preflight)
acquire = text.index("acquire_locks", preflight)
post_acquire_baseline = text.index("verify_runtime_baseline", acquire)
backup_mutation = text.index("MUTATION_STARTED=true", post_acquire_baseline)
backup = text.index("install -d -o root -g root -m 0700", backup_mutation)
replace = text.index("mv -Tf --", backup)
daemon_reload = text.index("systemctl daemon-reload", replace)
monitor_verify = text.rindex("/usr/local/sbin/rpi5-monitor")
assert initial_baseline < lock_probe < preflight < acquire < post_acquire_baseline < backup_mutation < backup < replace < daemon_reload < monitor_verify

assert len(re.findall(r"(?m)^systemctl daemon-reload$", text)) == 1
assert text.count("/usr/local/sbin/rpi5-post-reboot") >= 2
assert "\n/usr/local/sbin/rpi5-post-reboot\n" not in text

for forbidden_pattern in (
    r"(?m)^\s*systemctl\s+(?:restart|start|stop|enable|disable)\b",
    r"(?m)^\s*docker\s+(?:compose|restart)\b",
    r"(?m)^\s*apt-get\b",
    r"(?m)^\s*git\s+(?:pull|checkout)\b",
    r"(?m)^\s*(?:shutdown|reboot)\b",
    r"(?m)^\s*rm\s+-rf\b",
):
    assert re.search(forbidden_pattern, text) is None, forbidden_pattern

print("Health-gates activation source contract: PASS")
