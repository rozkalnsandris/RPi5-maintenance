#!/usr/bin/env bash
set -Eeuo pipefail
IFS=$'\n\t'

repo="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd -P)"
# shellcheck source=../ops/lib/rpi5-update-compose-health.sh
source "$repo/ops/lib/rpi5-update-compose-health.sh"

tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT
policy="$tmp/service-health.tsv"
cat >"$policy" <<'EOF'
# schema_version=1
# service_id	container_name	owner	lifecycle	required_state	docker_health	probe_type	probe_target	startup_grace_seconds	attempts	classification	rationale
db	db	test	production	running	absent	http	http://db.invalid/	0	1	required	synthetic HTTP gate
api	api	test	production	running	required	none	-	0	1	required	synthetic Docker-health gate
web	web	test	production	running	absent	exception	-	0	1	required	synthetic visible exception
EOF

export RPI5_SERVICE_HEALTH_LIB_PATH="$repo/ops/lib/rpi5-service-health.sh"
export RPI5_SERVICE_HEALTH_POLICY_FILE="$policy"
export RPI5_SERVICE_HEALTH_RETRY_DELAY_SECONDS=0

PROBE_RC=0
API_HEALTH=healthy

docker() {
    local command="${1-}" format container
    shift || true
    [[ "$command" == "inspect" ]] || return 2
    [[ "${1-}" == "-f" ]] || return 2
    format="${2-}"
    container="${3-}"
    case "$format" in
        '{{.State.Status}}')
            printf 'running\n'
            ;;
        '{{if .State.Health}}{{.State.Health.Status}}{{else}}none{{end}}')
            if [[ "$container" == "api" ]]; then
                printf '%s\n' "$API_HEALTH"
            else
                printf 'none\n'
            fi
            ;;
        '{{.State.StartedAt}}')
            printf '2026-01-01T00:00:00Z\n'
            ;;
        *)
            return 2
            ;;
    esac
}

rpi5_request_code_with_retry() {
    local target="${1-}"
    [[ "$target" == "http://db.invalid/" ]] || return 2
    return "$PROBE_RC"
}

expected=$'db\napi\nweb'
actual=$'db\napi\nweb'
rpi5_find_missing_compose_services "$expected" "$actual"
[[ -z "$RPI5_MISSING_COMPOSE_SERVICES" ]]
printf '%s\n' 'PASS complete-project-and-canonical-health'

actual=$'db\nweb'
if rpi5_find_missing_compose_services "$expected" "$actual"; then
    echo 'missing service was not detected' >&2
    exit 1
fi
[[ "$RPI5_MISSING_COMPOSE_SERVICES" == 'api' ]]
printf '%s\n' 'PASS one-missing-service'

actual=''
if rpi5_find_missing_compose_services "$expected" "$actual"; then
    echo 'empty runtime was not detected' >&2
    exit 1
fi
[[ "$RPI5_MISSING_COMPOSE_SERVICES" == $'db\napi\nweb' ]]
printf '%s\n' 'PASS all-services-missing'

actual=$'web\ndb\napi\napi'
rpi5_find_missing_compose_services "$expected" "$actual"
printf '%s\n' 'PASS runtime-order-and-duplicates-ignored'

PROBE_RC=1
if rpi5_find_missing_compose_services "$expected" "$expected"; then
    echo 'failed canonical HTTP probe was not rejected' >&2
    exit 1
fi
[[ "$RPI5_MISSING_COMPOSE_SERVICES" == *'db:probe-failed-grace-exhausted'* ]]
printf '%s\n' 'PASS canonical-http-probe-failure'

PROBE_RC=0
API_HEALTH=unhealthy
if rpi5_find_missing_compose_services "$expected" "$expected"; then
    echo 'unhealthy Docker health was not rejected' >&2
    exit 1
fi
[[ "$RPI5_MISSING_COMPOSE_SERVICES" == *'api:docker-unhealthy'* ]]
printf '%s\n' 'PASS canonical-docker-health-failure'

API_HEALTH=healthy
cat >>"$policy" <<'EOF'
orphan	orphan	test	production	running	required	none	-	0	1	required	not in expected project
EOF
rpi5_find_missing_compose_services "$expected" "$expected"
printf '%s\n' 'PASS policy-is-scoped-to-compose-project'

expected_with_unknown=$'db\napi\nweb\nunknown'
if rpi5_find_missing_compose_services "$expected_with_unknown" "$expected_with_unknown"; then
    echo 'Compose service without canonical policy row was not rejected' >&2
    exit 1
fi
[[ "$RPI5_MISSING_COMPOSE_SERVICES" == *'unknown:policy-row-missing'* ]]
printf '%s\n' 'PASS policy-row-required-for-every-compose-service'

printf '%s\n' 'Maintenance updater Compose health convergence tests: PASS (8 cases)'
