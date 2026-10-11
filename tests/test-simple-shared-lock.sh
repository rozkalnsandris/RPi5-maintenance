#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd -P)"
update="$ROOT/ops/bin/rpi5-update"
wrapper="$ROOT/ops/bin/rpi5-backup-serialized"
core="$ROOT/ops/bin/rpi5-backup"
library="$ROOT/ops/lib/rpi5-maintenance-locks.sh"

for f in "$update" "$wrapper" "$core" "$library"; do
  [[ -f "$f" && ! -L "$f" ]]
  bash -n "$f"
done

# Active updater and backup wrapper must acquire the same exclusive lock.
grep -Fq "LOCK_FILE='/run/lock/rpi5-maintenance-exclusive.lock'" "$update"
grep -Fq 'flock -n 9' "$update"
grep -Fq 'MAINTENANCE_LOCK_FILE="/run/lock/rpi5-maintenance-exclusive.lock"' "$wrapper"
grep -Fq 'rpi5_acquire_exclusive_lock' "$wrapper"
grep -Fq '"$BACKUP_CORE" "$@"' "$wrapper"
grep -Fq 'LOCK_FILE=/run/lock/rpi5-backup.lock' "$core"

# Isolated contention/release test; no production locks or backup run.
source "$library"
tmp="$(mktemp -d)"
trap 'rm -rf -- "$tmp"' EXIT
shared="$tmp/shared.lock"
holder_fd=""
rpi5_acquire_exclusive_lock "$shared" 1 holder_fd
[[ "$holder_fd" =~ ^[0-9]+$ ]]
blocked_fd=""
rc=0
rpi5_try_exclusive_lock "$shared" blocked_fd || rc=$?
[[ "$rc" -eq "$RPI5_LOCK_CONFLICT_RC" ]]
rpi5_release_exclusive_lock "$holder_fd"
rpi5_try_exclusive_lock "$shared" blocked_fd
[[ "$blocked_fd" =~ ^[0-9]+$ ]]
rpi5_release_exclusive_lock "$blocked_fd"
printf '%s\n' 'simple backup/update shared-lock PASS'
