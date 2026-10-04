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

printf '%s\n' 'simple update contract PASS'
