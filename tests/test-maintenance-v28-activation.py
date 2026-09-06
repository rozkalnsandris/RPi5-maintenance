#!/usr/bin/env python3
from __future__ import annotations
import subprocess
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
OP=ROOT/'ops/bin/rpi5-maintenance-v28-activate'
text=OP.read_text(encoding='utf-8')
subprocess.run(['bash','-n',str(OP)],check=True)

markers=(
"REPOSITORY='rozkalnsandris/RPi5-maintenance'",
"RELEASE_TAG='0.2.0'",
"EXPECTED_RELEASE_COMMIT='7a5685908e06cc35aa4bb623dd9fa6a3081c4416'",
"EXPECTED_V27_SHA256='f9c83acdd72131d6b696900972aa11d24978645b931846ff4ea8e6a8ed80bdc2'",
"EXPECTED_V27_COMPOSE_POLICY_SHA256='bc11a4f487efd791e23dc48f325e1aa396da14b67fc6e7429e300545ce954516'",
"EXPECTED_V28_SHA256='3a7898c1f06f7bd5b4136dd6875edf5c7178dad9c8ea4099ef065ce9b1c20882'",
"EXPECTED_V28_BLOB='1b647c26ba91d75aad29cf50ddc8d33a21c5e9c2'",
"EXPECTED_V28_COMPOSE_POLICY_SHA256='5ee19cbf09f5fa06853d1c121fea8216e1ae245aaa17af81e2affe6ab3aaae4f'",
"EXPECTED_V28_COMPOSE_POLICY_BLOB='b461423e2a45d9dc82905fb42afdc9dc16ae877b'",
"EXPECTED_V28_DOCKER_EVIDENCE_SHA256='f133adb38eb5499e1e582532f142f1b892ba99755262ce0612d8b21e96716456'",
"EXPECTED_V28_DOCKER_EVIDENCE_BLOB='52bc6afa2cc4f56be92ccd4c69243e5fd56208bf'",
"v28-docker-evidence-hardening-public-safe",
"V28_ACTIVATION_PREFLIGHT=PASS",
"MUTATION_PERFORMED=false",
"V28_HOST_ACTIVATION=PASS",
"V28_NON_MUTATING_APT_CHECK=PASS",
"MAINTENANCE_BOUNDARIES_UNCHANGED=PASS",
)
for m in markers: assert m in text,m

assert "--preflight|--apply" in text
assert "'$BROKER'" not in text and 'rozkalns-github-app-read-token' not in text
assert "urllib.request" in text and "releases/tags/{tag}" in text
assert "no successful exact-release main validate run" in text
assert "owner_git ls-remote origin refs/heads/main" in text
assert "owner_git fetch" not in text
assert 'release_sha="$(owner_git ls-remote origin "refs/tags/${RELEASE_TAG}"' in text

main=text[text.index('main() {'):]
preflight_exit='if [[ "$action" == \'--preflight\' ]]; then release_quiescent_window; echo \'MUTATION_PERFORMED=false\'; return 0; fi'
assert preflight_exit in main
assert main.index(preflight_exit) < main.index('mutation_started=true')
assert main.index('acquire_quiescent_window') < main.index(preflight_exit)

for m in (
'atomic_stage_from_release "$COMPOSE_POLICY_REL"',
'atomic_stage_from_release "$DOCKER_EVIDENCE_REL"',
'atomic_stage_from_release "$UPDATER_REL"',
'atomic_replace_stage "$compose_stage" "$COMPOSE_POLICY_DEST"',
'atomic_replace_stage "$docker_evidence_stage" "$DOCKER_EVIDENCE_DEST"',
'verify_v28_check "$updater_stage"',
'atomic_replace_stage "$updater_stage" "$UPDATER_DEST"',
): assert m in main,m
assert main.index('atomic_replace_stage "$compose_stage"') < main.index('verify_v28_check "$updater_stage"') < main.index('atomic_replace_stage "$updater_stage"')

on_exit=text[text.index('on_exit() {'):text.index('\nmain() {')]
for m in ('failed after the first host write','no automatic retry, rollback, cleanup, reboot, or alternate mutation was attempted','PRESERVED_STATE_DIR','PRESERVED_COMPOSE_STAGE','PRESERVED_DOCKER_EVIDENCE_STAGE'): assert m in on_exit,m
for forbidden in ('restore_activation_state','atomic_restore_snapshot','rm -f','systemctl reset-failed'): assert forbidden not in text,forbidden

for forbidden in ('systemctl start ','systemctl restart ','systemctl stop ','systemctl enable ','systemctl disable ','systemctl daemon-reload','docker compose ','apt-get update','apt-get upgrade','shutdown ',' reboot '):
    assert forbidden not in text,forbidden

for helper in ('rpi5-update-apt-policy.sh','rpi5-maintenance-locks.sh','rpi5-update-cleanup-policy.sh'):
    assert helper in text
assert 'unexpected docker-evidence helper exists before V28 activation' in text

idx=subprocess.check_output(['git','-C',str(ROOT),'ls-files','-s','--','ops/bin/rpi5-maintenance-v28-activate'],text=True).strip()
# Untracked during first local run is acceptable; after staging/CI it must be executable.
if idx: assert idx.split()[0]=='100755',idx

# Current tracked V28 bytes must still match the release-bound constants.
import hashlib
def sha(path: str) -> str:
    return hashlib.sha256((ROOT/path).read_bytes()).hexdigest()
assert sha('ops/bin/rpi5-update')=='3a7898c1f06f7bd5b4136dd6875edf5c7178dad9c8ea4099ef065ce9b1c20882'
assert sha('ops/lib/rpi5-update-compose-policy.sh')=='5ee19cbf09f5fa06853d1c121fea8216e1ae245aaa17af81e2affe6ab3aaae4f'
assert sha('ops/lib/rpi5-update-docker-evidence.sh')=='f133adb38eb5499e1e582532f142f1b892ba99755262ce0612d8b21e96716456'
assert subprocess.check_output(['git','-C',str(ROOT),'hash-object','ops/bin/rpi5-update'],text=True).strip()=='1b647c26ba91d75aad29cf50ddc8d33a21c5e9c2'
assert subprocess.check_output(['git','-C',str(ROOT),'hash-object','ops/lib/rpi5-update-compose-policy.sh'],text=True).strip()=='b461423e2a45d9dc82905fb42afdc9dc16ae877b'
assert subprocess.check_output(['git','-C',str(ROOT),'hash-object','ops/lib/rpi5-update-docker-evidence.sh'],text=True).strip()=='52bc6afa2cc4f56be92ccd4c69243e5fd56208bf'

print('Maintenance V28 activation source contract: PASS')
