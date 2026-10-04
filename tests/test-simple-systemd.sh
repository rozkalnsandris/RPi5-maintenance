#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd -P)"

update_service="$ROOT/ops/systemd/rpi5-update.service"
update_timer="$ROOT/ops/systemd/rpi5-update.timer"
monitor_service="$ROOT/ops/systemd/rpi5-monitor.service"
monitor_timer="$ROOT/ops/systemd/rpi5-monitor.timer"

for unit in "$update_service" "$monitor_service"; do
    grep -Fxq 'Type=oneshot' "$unit"
done
grep -Fxq 'OnSuccess=rpi5-maintenance-notify@success-%N.service' "$update_service"
grep -Fxq 'OnFailure=rpi5-maintenance-notify@failure-%N.service' "$update_service"
grep -Fxq 'OnFailure=rpi5-maintenance-notify@failure-%N.service' "$monitor_service"
grep -Fxq 'OnCalendar=Sun *-*-* 02:20:00' "$update_timer"
grep -Fxq 'Persistent=true' "$update_timer"
grep -Fxq 'OnCalendar=*-*-* 09:00:00' "$monitor_timer"
! grep -Fq 'AccuracySec=' "$update_timer"
! grep -Fq 'RandomizedDelaySec=' "$update_timer"
! grep -Fq 'AccuracySec=' "$monitor_timer"
! grep -Fq 'RandomizedDelaySec=' "$monitor_timer"

printf '%s\n' 'simple systemd contract PASS'
