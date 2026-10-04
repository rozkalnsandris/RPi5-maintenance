#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd -P)"
FILE="$ROOT/ops/bin/rpi5-monitor"

bash -n "$FILE"
grep -Fq 'docker.service ssh.service cloudflared.service' "$FILE"
grep -Fq 'docker compose config --services' "$FILE"
grep -Fq 'docker compose ps --services --status running' "$FILE"
grep -Fq 'docker ps --filter health=unhealthy' "$FILE"
grep -Fq 'docker ps --filter status=restarting' "$FILE"
grep -Fq 'DISK_FAIL_PERCENT="${DISK_FAIL_PERCENT:-90}"' "$FILE"

! grep -Fq 'service-health.tsv' "$FILE"
! grep -Fq 'curl ' "$FILE"
! grep -Fq 'https://' "$FILE"
! grep -Fq 'sleep ' "$FILE"

printf '%s\n' 'simple monitor contract PASS'
