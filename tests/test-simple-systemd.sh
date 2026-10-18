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


# Reviewable, opt-in journald source proposal. Not a deployed unit.
journal_proposal="$ROOT/config/journald-persistent.conf.example"
[[ -f "$journal_proposal" ]]
grep -Fxq '[Journal]' "$journal_proposal"
grep -Fxq 'Storage=persistent' "$journal_proposal"
grep -Fxq 'SystemMaxUse=128M' "$journal_proposal"
grep -Fxq 'SystemKeepFree=1G' "$journal_proposal"
grep -Fxq 'SystemMaxFileSize=16M' "$journal_proposal"
grep -Fxq 'MaxRetentionSec=14day' "$journal_proposal"
grep -Fq 'SOURCE-ONLY' "$journal_proposal"
# Do not allow example to mutate systemd automatically.
! grep -Eq '(^|[[:space:]])(systemctl|journalctl --flush|reboot|ExecStart)\b' "$journal_proposal"

printf '%s\n' 'simple systemd contract PASS'
