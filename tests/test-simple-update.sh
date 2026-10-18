#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd -P)"
FILE="$ROOT/ops/bin/rpi5-update"

bash -n "$FILE"
grep -Fq 'apt-get upgrade -y --with-new-pkgs --no-remove' "$FILE"
grep -Fq 'docker compose pull --ignore-buildable' "$FILE"
grep -Fq 'docker compose up -d --no-build --wait --wait-timeout 180' "$FILE"
grep -Fq 'docker image prune -f --filter "until=${retention_hours}h"' "$FILE"
grep -Fq 'docker buildx prune -f --filter "until=${retention_hours}h" --max-used-space "$BUILD_CACHE_MAX"' "$FILE"
grep -Fq 'REBOOT_POLICY="${REBOOT_POLICY:-if-needed}"' "$FILE"
grep -Fq 'if [[ -e /run/reboot-required ]]' "$FILE"

! grep -Fq 'docker system df' "$FILE"
! grep -Fq 'docker system prune' "$FILE"
! grep -Fq 'docker image prune -a' "$FILE"
! grep -Fq 'docker image prune --all' "$FILE"
! grep -Eq 'apt-get[^\n]*(autoremove|dist-upgrade|full-upgrade)' "$FILE"
! grep -Fq 'RETENTION_' "$FILE"
! grep -Fq 'CV_COMPOSE' "$FILE"
! grep -Fqi 'hermes' "$FILE"
! grep -Fq 'rclone selfupdate' "$FILE"

# Simulate recovery after Docker and its local DNS restart. No live Docker/APT calls.
grep -Fq "phase='docker-ready'" "$FILE"
grep -Fq 'timeout 5 getent ahostsv4 auth.docker.io' "$FILE"
grep -Fq 'wait_for_post_apt_docker_dns' "$FILE"
[[ "$(grep -Fc 'docker compose pull --ignore-buildable' "$FILE")" -eq 1 ]]

readiness_fn="$(sed -n '/^wait_for_post_apt_docker_dns() {/,/^}/p' "$FILE")"
[[ -n "$readiness_fn" && "$readiness_fn" == *'12 checks'* ]]
eval "$readiness_fn"

(
    log() { :; }
    fail() { return 75; }
    docker_checks=0
    dns_checks=0
    sleeps=0
    timeout() {
        [[ "$1" == 5 ]] || return 99
        case "$2" in
            docker)
                [[ "$3" == info ]] || return 99
                docker_checks=$((docker_checks + 1))
                (( docker_checks > 1 ))
                ;;
            getent)
                [[ "$3" == ahostsv4 && "$4" == auth.docker.io ]] || return 99
                dns_checks=$((dns_checks + 1))
                (( dns_checks > 2 ))
                ;;
            *) return 99 ;;
        esac
    }
    sleep() { [[ "$1" == 5 ]] || return 99; sleeps=$((sleeps + 1)); }
    wait_for_post_apt_docker_dns
    [[ "$docker_checks" -eq 5 && "$dns_checks" -eq 4 && "$sleeps" -eq 4 ]]
)

# A persistent DNS failure must stop before the image pull; no pull retry.
(
    log() { :; }
    fail() { return 75; }
    dns_checks=0
    sleeps=0
    timeout() {
        [[ "$1" == 5 ]] || return 99
        case "$2" in
            docker) return 0 ;;
            getent) dns_checks=$((dns_checks + 1)); return 1 ;;
            *) return 99 ;;
        esac
    }
    sleep() { [[ "$1" == 5 ]] || return 99; sleeps=$((sleeps + 1)); }
    if wait_for_post_apt_docker_dns; then
        echo 'DNS gate unexpectedly passed' >&2
        exit 1
    else
        [[ "$?" -eq 75 ]]
    fi
    [[ "$dns_checks" -eq 12 && "$sleeps" -eq 11 ]]
)

# Synthetic ENOSPC-like phase failure. Reuse the real updater ERR handler
# in a separate bash process; never run APT, Docker, systemd or fill /tmp.
error_handler="$(sed -n '/^on_error() {/,/^}/p' "$FILE")"
[[ -n "$error_handler" ]]
set +e
failure_output="$(bash -c '
    set -Eeuo pipefail
    eval "$1"
    trap on_error ERR
    phase="cleanup"
    log() { printf "%s\\n" "$*"; }
    printf "%s\\n" "No space left on device" >&2
    false
    printf "%s\\n" "UNREACHABLE_MONITOR_OR_REBOOT"
' bash "$error_handler" 2>&1)"
failure_rc=$?
set -e
[[ "$failure_rc" -eq 1 ]]
[[ "$failure_output" == *'FAIL phase=cleanup rc=1'* ]]
[[ "$failure_output" != *'UNREACHABLE_MONITOR_OR_REBOOT'* ]]


# Restore screenshot-style notices without broad CV/Hermes/public monitoring.
grep -Fq 'compose_images_snapshot' "$FILE"
grep -Fq 'write_weekly_report' "$FILE"
grep -Fq 'journalctl "_SYSTEMD_INVOCATION_ID=$invocation"' "$FILE"
grep -Fq 'rpi5-maintenance-notify@start-rpi5-update.service.service' "$FILE"
grep -Fq 'OnSuccess=rpi5-maintenance-notify@success-%N.service' "$ROOT/ops/systemd/rpi5-update.service"
grep -Fq 'MONITOR_INVOCATION_ID' "$ROOT/ops/bin/rpi5-maintenance-notify"
grep -Fq '/run/rpi5-maintenance-reports/' "$ROOT/ops/bin/rpi5-maintenance-notify"
grep -Fq 'stat -c' "$ROOT/ops/bin/rpi5-maintenance-notify"
! grep -Fqi 'hermes' "$FILE"
! grep -Fq 'CV_COMPOSE' "$FILE"
! grep -Fq 'docker system prune' "$FILE"

printf '%s\n' 'simple update contract PASS'
