#!/usr/bin/env bash
# Shared service-health classification helpers for RPi5 maintenance health gates.

RPI5_HEALTH_CLASS=""
RPI5_HEALTH_REASON=""

rpi5_service_health_classify() {
    local enforcement="${1:?missing enforcement}"
    local required_state="${2:?missing required_state}"
    local docker_policy="${3:?missing docker_health policy}"
    local probe_type="${4:?missing probe_type}"
    local state="${5:-missing}"
    local health="${6:-none}"
    local age_seconds="${7:-0}"
    local grace_seconds="${8:-0}"
    local probe_rc="${9:-2}"

    RPI5_HEALTH_CLASS=""
    RPI5_HEALTH_REASON=""

    [[ "$age_seconds" =~ ^[0-9]+$ && "$grace_seconds" =~ ^[0-9]+$ ]] || {
        RPI5_HEALTH_CLASS="FAIL_PERSISTENT"
        RPI5_HEALTH_REASON="invalid-age-or-grace"
        return 0
    }

    if [[ "$enforcement" == "observe" ]]; then
        RPI5_HEALTH_CLASS="OBSERVE"
        RPI5_HEALTH_REASON="owner-observe"
        return 0
    fi
    [[ "$enforcement" == "required" ]] || {
        RPI5_HEALTH_CLASS="FAIL_PERSISTENT"
        RPI5_HEALTH_REASON="invalid-enforcement"
        return 0
    }

    if [[ "$state" != "$required_state" ]]; then
        if [[ "$state" == "missing" ]] && (( age_seconds < grace_seconds )); then
            RPI5_HEALTH_CLASS="TRANSIENT"
            RPI5_HEALTH_REASON="state-missing-within-grace"
        else
            RPI5_HEALTH_CLASS="FAIL_PERSISTENT"
            RPI5_HEALTH_REASON="state-${state:-missing}"
        fi
        return 0
    fi

    case "$health" in
        unhealthy)
            RPI5_HEALTH_CLASS="FAIL_PERSISTENT"
            RPI5_HEALTH_REASON="docker-unhealthy"
            return 0
            ;;
        starting)
            if (( age_seconds < grace_seconds )); then
                RPI5_HEALTH_CLASS="TRANSIENT"
                RPI5_HEALTH_REASON="docker-starting"
            else
                RPI5_HEALTH_CLASS="FAIL_PERSISTENT"
                RPI5_HEALTH_REASON="docker-starting-grace-exhausted"
            fi
            return 0
            ;;
        healthy|none|"") ;;
        *)
            RPI5_HEALTH_CLASS="FAIL_PERSISTENT"
            RPI5_HEALTH_REASON="docker-health-${health}"
            return 0
            ;;
    esac

    if [[ "$docker_policy" == "required" && "$health" != "healthy" ]]; then
        RPI5_HEALTH_CLASS="FAIL_PERSISTENT"
        RPI5_HEALTH_REASON="docker-health-missing"
        return 0
    fi
    [[ "$docker_policy" == "required" || "$docker_policy" == "absent" ]] || {
        RPI5_HEALTH_CLASS="FAIL_PERSISTENT"
        RPI5_HEALTH_REASON="invalid-docker-policy"
        return 0
    }

    case "$probe_type" in
        exception)
            RPI5_HEALTH_CLASS="OBSERVE"
            RPI5_HEALTH_REASON="explicit-exception"
            ;;
        none)
            if [[ "$docker_policy" == "required" && "$health" == "healthy" ]]; then
                RPI5_HEALTH_CLASS="PASS"
                RPI5_HEALTH_REASON="docker-healthy"
            else
                RPI5_HEALTH_CLASS="FAIL_PERSISTENT"
                RPI5_HEALTH_REASON="no-application-proof"
            fi
            ;;
        http|tcp)
            case "$probe_rc" in
                0)
                    RPI5_HEALTH_CLASS="PASS"
                    RPI5_HEALTH_REASON="probe-pass"
                    ;;
                1)
                    if (( age_seconds < grace_seconds )); then
                        RPI5_HEALTH_CLASS="TRANSIENT"
                        RPI5_HEALTH_REASON="probe-failed-within-grace"
                    else
                        RPI5_HEALTH_CLASS="FAIL_PERSISTENT"
                        RPI5_HEALTH_REASON="probe-failed-grace-exhausted"
                    fi
                    ;;
                *)
                    RPI5_HEALTH_CLASS="FAIL_PERSISTENT"
                    RPI5_HEALTH_REASON="probe-infrastructure-error"
                    ;;
            esac
            ;;
        *)
            RPI5_HEALTH_CLASS="FAIL_PERSISTENT"
            RPI5_HEALTH_REASON="invalid-probe-type"
            ;;
    esac
}

rpi5_service_health_policy_max_grace() {
    local policy_file="${1:?missing policy file}"
    local service_id container_name owner lifecycle required_state docker_health
    local probe_type probe_target grace attempts classification rationale
    local max_grace=0

    while IFS=$'\t' read -r service_id container_name owner lifecycle required_state docker_health probe_type probe_target grace attempts classification rationale; do
        [[ -n "$service_id" && "$service_id" != \#* ]] || continue
        [[ "$grace" =~ ^[0-9]+$ ]] || return 2
        (( grace > max_grace )) && max_grace="$grace"
    done <"$policy_file"

    printf '%s' "$max_grace"
}
