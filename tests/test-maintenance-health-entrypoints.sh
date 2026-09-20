#!/usr/bin/env bash
set -Eeuo pipefail
IFS=$'\n\t'

repo="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd -P)"
monitor="$repo/ops/bin/rpi5-monitor"
post="$repo/ops/bin/rpi5-post-reboot"
health_lib="$repo/ops/lib/rpi5-maintenance-health.sh"
service_health_lib="$repo/ops/lib/rpi5-service-health.sh"
policy="$repo/ops/config/service-health.tsv"

for f in "$monitor" "$post" "$health_lib" "$service_health_lib" "$policy"; do
    [[ -f "$f" && ! -L "$f" ]]
done
for f in "$monitor" "$post" "$health_lib" "$service_health_lib"; do
    bash -n "$f"
done

for f in "$monitor" "$post"; do
    grep -Fq 'must run as root' "$f"
    grep -Fq '/usr/local/lib/rpi5-maintenance' "$f"
    ! grep -Fq '/usr/local/libexec/rpi5-maintenance' "$f"
    grep -Fq '/etc/rpi5-maintenance/service-health.tsv' "$f"
    grep -Fq 'rpi5-service-health.sh' "$f"
    grep -Fq 'rpi5_service_health_classify' "$f"
    grep -Fq 'FAIL_PERSISTENT' "$f"
    grep -Fq 'TRANSIENT' "$f"
    grep -Fq 'OBSERVE' "$f"
    grep -Fq "docker ps -a --format '{{.Names}}\\t{{.State}}\\t{{.HealthStatus}}'" "$f"
    ! grep -Fq '/etc/rpi5-maintenance/required-containers' "$f"
    ! grep -Fq 'rpi5_validate_required_container_inventory' "$f"
    if grep -Eq '/home/[A-Za-z0-9._-]+/|192\.168\.|10\.[0-9]|172\.(1[6-9]|2[0-9]|3[01])\.' "$f"; then
        echo "private runtime literal found in $f" >&2
        exit 1
    fi
    if grep -Eq 'TELEGRAM_(TOKEN|CHAT_ID)|/etc/rpi-update\.conf|/var/log/rpi5-(monitor|post-reboot)' "$f"; then
        echo "health entrypoint crosses secret/file-log boundary: $f" >&2
        exit 1
    fi
done

grep -Fq 'rpi5_service_health_policy_max_grace' "$monitor"
grep -Fq 'rpi5_service_health_policy_max_grace' "$post"
grep -Fq 'state="${states[$container_name]:-missing}"' "$post"
grep -Fq 'age=0' "$post"

grep -Fq $'cv\tcv\trozkalns_cv\tproduction\trunning\tabsent\thttp\thttp://127.0.0.1:8088/' "$policy"
grep -Fq $'hermes-blog\thermes-blog\tRPi5-maintenance\tproduction\trunning\tabsent\thttp\thttp://127.0.0.1:8089/' "$policy"

grep -Fq 'https://rozkalns.net/' "$monitor"
grep -Fq 'https://tech.rozkalns.net/' "$monitor"
grep -Fq 'https://rozkalns.net/' "$post"
grep -Fq 'https://tech.rozkalns.net/' "$post"
! grep -Fq 'cron.service' "$monitor"
! grep -Fq 'cron.service' "$post"
! grep -Eq 'pgrep|backup\.sh|update\.sh' "$monitor"
! grep -Eq 'pgrep|backup\.sh|update\.sh' "$post"

printf '%s\n' 'Maintenance health entrypoint contract: PASS'
