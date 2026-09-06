#!/usr/bin/env bash
set -Eeuo pipefail
IFS=$'\n\t'

repo="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd -P)"
fixture="$repo/tests/fixtures/docker-maintenance-2026-09-06.env"
# shellcheck source=../ops/lib/rpi5-update-compose-policy.sh
source "$repo/ops/lib/rpi5-update-compose-policy.sh"
# shellcheck source=../ops/lib/rpi5-update-docker-evidence.sh
source "$repo/ops/lib/rpi5-update-docker-evidence.sh"
# shellcheck source=fixtures/docker-maintenance-2026-09-06.env
source "$fixture"

tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT
project="$tmp/project"
mkdir -p "$project"

rpi5_compose_service_inventory() {
    printf '%s\n' "${FIXTURE_SERVICE}"$'\tregistry\teclipse-mosquitto:2'
}

rpi5_compose_service_container_id() {
    [[ "$2" == "$FIXTURE_SERVICE" ]] || return 2
    if [[ "$FIXTURE_SERVICE_RUNNING_AT_TARGET_SELECTION" == 'yes' ]]; then
        printf 'container-%s\n' "$2"
    fi
}

if rpi5_select_compose_update_targets "$project"; then
    echo 'incident fixture unexpectedly selected reconcile targets' >&2
    exit 1
else
    rc=$?
fi
[[ "$rc" -eq "$FIXTURE_EXPECT_SELECTION_RC" ]]
[[ "$RPI5_COMPOSE_SELECTION_FAILURE_REASON" == "$FIXTURE_EXPECT_REASON" ]]
[[ "$RPI5_COMPOSE_SELECTION_FAILURE_SERVICE" == "$FIXTURE_SERVICE" ]]

line="$(rpi5_docker_evidence_line \
    20260906_022000 "$FIXTURE_PROJECT" "$FIXTURE_EXPECT_PHASE" \
    compose-target-selection failed "$rc" changed \
    "$RPI5_COMPOSE_SELECTION_FAILURE_REASON" "$RPI5_COMPOSE_SELECTION_FAILURE_SERVICE" \
    100 105)"
[[ "$line" == *'"phase":"target-selection"'* ]]
[[ "$line" == *'"command":"compose-target-selection"'* ]]
[[ "$line" == *'"reason":"missing-running-container"'* ]]
[[ "$line" == *'"service":"mosquitto"'* ]]
[[ "$line" == *'"mutation":"changed"'* ]]
[[ "$line" == *'"duration_seconds":5'* ]]

redacted="$(rpi5_docker_evidence_token $'unsafe token\nsecret')"
[[ "$redacted" == 'redacted' ]]

before="$tmp/before.tsv"
after="$tmp/after.tsv"
printf '%s\n' $'image:stable\tsha256:old\t1' >"$before"
cp "$before" "$after"
[[ "$(rpi5_docker_snapshot_mutation_state "$before" "$after")" == 'none' ]]
printf '%s\n' $'image:stable\tsha256:new\t2' >"$after"
[[ "$(rpi5_docker_snapshot_mutation_state "$before" "$after")" == 'changed' ]]
[[ "$(rpi5_docker_snapshot_mutation_state "$before" "$tmp/missing")" == 'unknown' ]]

docker() {
    if [[ "$1 $2 $3" == 'compose config --services' ]]; then
        printf '%s\n' mosquitto grafana
    elif [[ "$1 $2 $3" == 'compose ps -aq' ]]; then
        case "${4:-}" in
            mosquitto) printf '%s\n' cid-mosquitto ;;
            grafana) : ;;
            *) return 2 ;;
        esac
    elif [[ "$1 $2" == 'inspect --format' && "${4:-}" == 'cid-mosquitto' ]]; then
        case "$3" in
            '{{.Id}}') printf '%s\n' 'cid-mosquitto' ;;
            '{{.State.Running}}') printf '%s\n' 'false' ;;
            '{{if .State.Health}}{{.State.Health.Status}}{{else}}none{{end}}') printf '%s\n' 'none' ;;
            '{{.Image}}') printf '%s\n' 'sha256:mosquitto' ;;
            *) return 2 ;;
        esac
    else
        return 2
    fi
}
state="$tmp/state.tsv"
rpi5_snapshot_compose_state "$project" "$state"
grep -Fxq $'mosquitto\tcid-mosquitto\tfalse\tnone\tsha256:mosquitto' "$state"
grep -Fxq $'grafana\tMISSING\tfalse\tnone\tMISSING' "$state"
unset -f docker

capture="$tmp/capture.log"
set +e
rpi5_capture_command_evidence "$capture" "$project" bash -c 'printf "stdout-line\\n"; printf "stderr-line\\n" >&2; exit 17' >/dev/null
capture_rc=$?
set -e
[[ "$capture_rc" -eq 17 ]]
grep -Fxq 'stdout-line' "$capture"
grep -Fxq 'stderr-line' "$capture"

printf '%s\n' 'context deadline exceeded while waiting for services' >"$tmp/readiness.log"
[[ "$(rpi5_docker_failure_reason_from_log "$tmp/readiness.log" 1 compose-up-command-failed)" == 'readiness-timeout' ]]
[[ "$(rpi5_docker_failure_reason_from_log "$tmp/readiness.log" 124 pull-command-failed)" == 'command-timeout' ]]
printf '%s\n' 'ordinary failure' >"$tmp/failure.log"
[[ "$(rpi5_docker_failure_reason_from_log "$tmp/failure.log" 17 compose-up-command-failed)" == 'compose-up-command-failed' ]]

updater="$repo/ops/bin/rpi5-update"
grep -Fq 'rpi5-update-docker-evidence.sh' "$updater"
grep -Fq 'rpi5_docker_evidence_line' "$updater"
grep -Fq 'rpi5_capture_command_evidence' "$updater"

bash -n "$repo/ops/lib/rpi5-update-docker-evidence.sh"
bash -n "$repo/ops/lib/rpi5-update-compose-policy.sh"
bash -n "$updater"

printf '%s\n' 'Maintenance updater Docker evidence regression: PASS'
