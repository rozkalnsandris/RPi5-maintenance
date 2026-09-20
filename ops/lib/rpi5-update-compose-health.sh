#!/usr/bin/env bash
# Compose completeness and canonical health helpers for the weekly updater.

RPI5_MISSING_COMPOSE_SERVICES=""
RPI5_COMPOSE_HEALTH_FAILURES=""

rpi5_compose_health_controlled_file() {
    local path="${1:?missing path}" uid mode expected_uid
    [[ -f "$path" && ! -L "$path" ]] || return 1
    uid="$(stat -c '%u' "$path")"
    mode="$(stat -c '%a' "$path")"
    expected_uid="${EUID:-$(id -u)}"
    [[ "$uid" -eq "$expected_uid" ]] || return 1
    (( (8#$mode & 022) == 0 ))
}

rpi5_compose_health_load_policy() {
    local lib="${RPI5_SERVICE_HEALTH_LIB_PATH:-/usr/local/lib/rpi5-maintenance/rpi5-service-health.sh}"
    local policy="${RPI5_SERVICE_HEALTH_POLICY_FILE:-/etc/rpi5-maintenance/service-health.tsv}"

    rpi5_compose_health_controlled_file "$lib" || {
        RPI5_COMPOSE_HEALTH_FAILURES="health-policy:unsafe-or-missing-classifier"
        return 1
    }
    rpi5_compose_health_controlled_file "$policy" || {
        RPI5_COMPOSE_HEALTH_FAILURES="health-policy:unsafe-or-missing-policy"
        return 1
    }

    if ! declare -F rpi5_service_health_classify >/dev/null 2>&1; then
        # shellcheck source=/dev/null
        source "$lib"
    fi
    declare -F rpi5_service_health_classify >/dev/null 2>&1 || {
        RPI5_COMPOSE_HEALTH_FAILURES="health-policy:classifier-unavailable"
        return 1
    }

    RPI5_COMPOSE_HEALTH_POLICY_FILE="$policy"
}

rpi5_compose_health_container_age_seconds() {
    local container_name="${1:?missing container name}" grace="${2:?missing grace}"
    local started_at started_epoch now

    started_at="$(docker inspect -f '{{.State.StartedAt}}' "$container_name" 2>/dev/null || true)"
    started_epoch="$(date -d "$started_at" +%s 2>/dev/null || true)"
    now="$(date +%s)"
    if [[ "$started_epoch" =~ ^[0-9]+$ && "$now" =~ ^[0-9]+$ && "$now" -ge "$started_epoch" ]]; then
        printf '%s' "$((now - started_epoch))"
    else
        # Unknown age must not extend startup grace.
        printf '%s' "$grace"
    fi
}

rpi5_compose_health_probe() {
    local probe_type="${1:?missing probe type}"
    local target="${2-}"
    local attempts="${3:?missing attempts}"
    local host port code probe_rc

    case "$probe_type" in
        http)
            declare -F rpi5_request_code_with_retry >/dev/null 2>&1 || return 2
            probe_rc=0
            code="$(rpi5_request_code_with_retry "$target" "$attempts" 1)" || probe_rc=$?
            case "$probe_rc" in
                0) return 0 ;;
                1) return 1 ;;
                *) return 2 ;;
            esac
            ;;
        tcp)
            host="${target%:*}"
            port="${target##*:}"
            [[ "$host" =~ ^[A-Za-z0-9._-]+$ &&
               "$port" =~ ^[0-9]+$ &&
               "$attempts" =~ ^[1-9][0-9]*$ ]] || return 2
            local attempt
            for ((attempt = 1; attempt <= attempts; attempt++)); do
                if timeout 3 bash -c "exec 3<>/dev/tcp/${host}/${port}" 2>/dev/null; then
                    return 0
                fi
                (( attempt == attempts )) || sleep 1
            done
            return 1
            ;;
        none|exception)
            return 2
            ;;
        *)
            return 2
            ;;
    esac
}

rpi5_compose_health_evaluate_once() {
    local expected="${1-}" service
    local service_id container_name owner lifecycle required_state docker_health
    local probe_type probe_target grace attempts enforcement rationale
    local state health age probe_rc
    local persistent=0 transient=0 matched_count
    local -a failures=()
    local -A expected_services=()
    local -A matched=()

    while IFS= read -r service; do
        [[ -n "$service" ]] || continue
        expected_services["$service"]=1
    done <<<"$expected"

    while IFS=$'\t' read -r service_id container_name owner lifecycle required_state docker_health probe_type probe_target grace attempts enforcement rationale; do
        [[ -n "$service_id" && "$service_id" != \#* ]] || continue
        [[ -n "${expected_services[$service_id]:-}" ]] || continue

        matched_count="${matched[$service_id]:-0}"
        matched_count=$((matched_count + 1))
        matched["$service_id"]="$matched_count"
        if (( matched_count > 1 )); then
            failures+=("${service_id}:duplicate-policy-row")
            persistent=1
            continue
        fi

        if [[ ! "$grace" =~ ^[0-9]+$ || ! "$attempts" =~ ^[1-9][0-9]*$ ]]; then
            failures+=("${service_id}:invalid-policy-numeric-field")
            persistent=1
            continue
        fi

        if [[ "$enforcement" == "observe" ]]; then
            state="missing"
            health="none"
            age="$grace"
            probe_rc=2
        else
            state="$(docker inspect -f '{{.State.Status}}' "$container_name" 2>/dev/null || true)"
            if [[ -z "$state" ]]; then
                state="missing"
                health="none"
                age="$grace"
            else
                health="$(docker inspect -f '{{if .State.Health}}{{.State.Health.Status}}{{else}}none{{end}}' "$container_name" 2>/dev/null || true)"
                [[ -n "$health" ]] || health="none"
                age="$(rpi5_compose_health_container_age_seconds "$container_name" "$grace")"
            fi

            probe_rc=2
            if [[ "$state" == "running" ]]; then
                case "$probe_type" in
                    http|tcp)
                        probe_rc=0
                        rpi5_compose_health_probe "$probe_type" "$probe_target" "$attempts" || probe_rc=$?
                        ;;
                    none|exception)
                        probe_rc=2
                        ;;
                    *)
                        probe_rc=2
                        ;;
                esac
            fi
        fi

        rpi5_service_health_classify \
            "$enforcement" "$required_state" "$docker_health" "$probe_type" \
            "$state" "$health" "$age" "$grace" "$probe_rc"

        case "$RPI5_HEALTH_CLASS" in
            PASS|OBSERVE)
                ;;
            TRANSIENT)
                transient=1
                printf '[health] TRANSIENT service=%s container=%s reason=%s\n' \
                    "$service_id" "$container_name" "$RPI5_HEALTH_REASON" >&2
                ;;
            FAIL_PERSISTENT)
                failures+=("${service_id}:${RPI5_HEALTH_REASON}")
                persistent=1
                ;;
            *)
                failures+=("${service_id}:invalid-classification")
                persistent=1
                ;;
        esac
    done <"$RPI5_COMPOSE_HEALTH_POLICY_FILE"

    while IFS= read -r service; do
        [[ -n "$service" ]] || continue
        if [[ "${matched[$service]:-0}" -eq 0 ]]; then
            failures+=("${service}:policy-row-missing")
            persistent=1
        fi
    done <<<"$expected"

    if (( persistent != 0 )); then
        RPI5_COMPOSE_HEALTH_FAILURES="$(IFS=,; printf '%s' "${failures[*]}")"
        return 1
    fi
    if (( transient != 0 )); then
        RPI5_COMPOSE_HEALTH_FAILURES="transient"
        return 75
    fi

    RPI5_COMPOSE_HEALTH_FAILURES=""
    return 0
}

rpi5_validate_compose_service_health_policy() {
    local expected="${1-}" policy_rc now deadline max_grace delay remaining

    RPI5_COMPOSE_HEALTH_FAILURES=""
    rpi5_compose_health_load_policy || return 1
    max_grace="$(rpi5_service_health_policy_max_grace "$RPI5_COMPOSE_HEALTH_POLICY_FILE")" || {
        RPI5_COMPOSE_HEALTH_FAILURES="health-policy:invalid-policy"
        return 1
    }
    [[ "$max_grace" =~ ^[0-9]+$ ]] || {
        RPI5_COMPOSE_HEALTH_FAILURES="health-policy:invalid-max-grace"
        return 1
    }

    delay="${RPI5_SERVICE_HEALTH_RETRY_DELAY_SECONDS:-10}"
    [[ "$delay" =~ ^[0-9]+$ ]] || {
        RPI5_COMPOSE_HEALTH_FAILURES="health-policy:invalid-retry-delay"
        return 1
    }

    now="$(date +%s)"
    deadline="$((now + max_grace))"

    while true; do
        policy_rc=0
        rpi5_compose_health_evaluate_once "$expected" || policy_rc=$?
        case "$policy_rc" in
            0)
                return 0
                ;;
            1)
                printf '[health] FAIL_PERSISTENT %s\n' "$RPI5_COMPOSE_HEALTH_FAILURES" >&2
                return 1
                ;;
            75)
                now="$(date +%s)"
                if (( now >= deadline )); then
                    RPI5_COMPOSE_HEALTH_FAILURES="health-policy:transient-deadline-exhausted"
                    printf '[health] FAIL_PERSISTENT %s\n' "$RPI5_COMPOSE_HEALTH_FAILURES" >&2
                    return 1
                fi
                remaining="$((deadline - now))"
                (( delay > remaining )) && delay="$remaining"
                printf '[health] retry transient project health in %ss\n' "$delay" >&2
                sleep "$delay"
                ;;
            *)
                RPI5_COMPOSE_HEALTH_FAILURES="health-policy:unexpected-classifier-rc-${policy_rc}"
                return 1
                ;;
        esac
    done
}

# Compare newline-separated expected service names from
# `docker compose config --services` with the newline-separated service names
# that currently have containers according to `docker compose ps --all --services`.
# Sets RPI5_MISSING_COMPOSE_SERVICES to a newline-separated list in expected
# configuration order. Once completeness passes, the same call also enforces the
# canonical service-health policy for that Compose project. Health failures are
# surfaced through the same fail-closed return path as a `health-policy:` marker
# because the V28 updater already consumes this helper as its convergence gate.
rpi5_find_missing_compose_services() {
    local expected="${1-}"
    local actual="${2-}"
    local service
    local -A actual_services=()
    local -a missing=()

    while IFS= read -r service; do
        [[ -n "$service" ]] || continue
        actual_services["$service"]=1
    done <<<"$actual"

    while IFS= read -r service; do
        [[ -n "$service" ]] || continue
        [[ -n "${actual_services[$service]:-}" ]] || missing+=("$service")
    done <<<"$expected"

    RPI5_MISSING_COMPOSE_SERVICES="$(printf '%s\n' "${missing[@]:-}")"
    RPI5_MISSING_COMPOSE_SERVICES="${RPI5_MISSING_COMPOSE_SERVICES%$'\n'}"

    if (( ${#missing[@]} != 0 )); then
        return 1
    fi

    if ! rpi5_validate_compose_service_health_policy "$expected"; then
        RPI5_MISSING_COMPOSE_SERVICES="health-policy:${RPI5_COMPOSE_HEALTH_FAILURES}"
        return 1
    fi

    RPI5_MISSING_COMPOSE_SERVICES=""
    return 0
}
