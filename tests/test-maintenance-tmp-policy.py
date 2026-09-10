#!/usr/bin/env python3
from __future__ import annotations

import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OP = ROOT / 'ops/bin/rpi5-tmp-policy-activate'
DOC = ROOT / 'docs/TMP_POLICY.md'

text = OP.read_text(encoding='utf-8')
doc = DOC.read_text(encoding='utf-8')
subprocess.run(['bash', '-n', str(OP)], check=True)

markers = (
    "EXPECTED_HOST='rpi5'",
    "FSTAB='/etc/fstab'",
    "TMPFILES_DEST='/etc/tmpfiles.d/tmp.conf'",
    "TMP_MOUNT_MASK='/etc/systemd/system/tmp.mount'",
    "tmpfs /tmp tmpfs defaults,strictatime,nosuid,nodev,mode=1777,size=50% 0 0",
    "D /tmp 1777 root root 14d",
    '--preflight|--apply|--verify',
    'TMP_POLICY_PREFLIGHT=PASS',
    'TMP_POLICY_STAGE=PASS',
    'TMP_POLICY_POST_REBOOT_VERIFY=PASS',
    'REBOOT_REQUIRED_FOR_TMP_POLICY=true',
    'PRESERVED_STATE_DIR=',
)
for marker in markers:
    assert marker in text, marker

assert "persistent=\"$(persistent_state)\"" in text
assert "runtime=\"$(runtime_state)\"" in text
assert "[[ \"$persistent\" == legacy && \"$runtime\" == tmpfs-active ]]" in text
assert "[[ \"$persistent\" == policy-installed && \"$runtime\" == disk-backed ]]" in text
assert "[[ \"$(stat -c '%a' /tmp)\" == '1777' ]]" in text

main = text[text.index('main() {'):]
assert main.index("if [[ \"$action\" == '--preflight' ]]") < main.index('mutation_started=true')
assert main.index("if [[ \"$action\" == '--verify' ]]") < main.index('mutation_started=true')
assert main.index('mutation_started=true') < main.index('state_dir="$(mktemp -d /root/rpi5-tmp-policy-XXXXXXXX)"')
assert main.index('write_candidates') < main.index('install_policy')

on_exit = text[text.index('on_exit() {'):text.index('\ncount_exact_line()')]
for marker in (
    'failed after the first host write',
    'no automatic retry, rollback, cleanup, unmount, service restart, or reboot was attempted',
    'PRESERVED_STATE_DIR',
):
    assert marker in on_exit, marker

for forbidden in (
    '\numount ',
    '\nmount -o remount',
    '\nsystemctl restart ',
    '\nsystemctl start ',
    '\nsystemctl stop ',
    '\nsystemctl daemon-reload',
    '\ndocker ',
    '\napt-get ',
    '\nrm -rf',
    '\nshutdown ',
    '\nreboot ',
):
    assert forbidden not in text, forbidden

for doc_marker in (
    '2026-09-10',
    'no space left on device',
    'NVMe-backed root filesystem',
    '14-day retention',
    'Debian 13 release notes',
    'Filesystem Hierarchy Standard',
    'No rollback is automatic',
):
    assert doc_marker in doc, doc_marker

idx = subprocess.check_output(
    ['git', '-C', str(ROOT), 'ls-files', '-s', '--', 'ops/bin/rpi5-tmp-policy-activate'],
    text=True,
).strip()
if idx:
    assert idx.split()[0] == '100755', idx

print('Maintenance /tmp policy source contract: PASS')
