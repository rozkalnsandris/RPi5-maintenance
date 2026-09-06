#!/usr/bin/env bash
# Structured, sanitized Docker evidence helpers for the weekly updater.

rpi5_docker_evidence_token() {
    local value="${1:-none}"
    if [[ "$value" =~ ^[A-Za-z0-9._:-]+$ ]]; then
        printf '%s' "$value"
    else
        printf '%s' 'redacted'
    fi
}

rpi5_docker_evidence_line() {
    local run_id="${1:?missing run id}"
    local project="${2:?missing project}"
    local phase="${3:?missing phase}"
    local command_id="${4:?missing command id}"
    local outcome="${5:?missing outcome}"
    local rc="${6:?missing rc}"
    local mutation="${7:?missing mutation}"
    local reason="${8:-none}"
    local service="${9:-none}"
    local started_epoch="${10:-0}"
    local ended_epoch="${11:-0}"
    local duration_seconds=0

    [[ "$rc" =~ ^[0-9]+$ ]] || rc=255
    [[ "$started_epoch" =~ ^[0-9]+$ ]] || started_epoch=0
    [[ "$ended_epoch" =~ ^[0-9]+$ ]] || ended_epoch=0
    if (( ended_epoch >= started_epoch )); then
        duration_seconds=$((ended_epoch - started_epoch))
    fi

    printf '{"run_id":"%s","project":"%s","phase":"%s","command":"%s","outcome":"%s","rc":%s,"mutation":"%s","reason":"%s","service":"%s","started_epoch":%s,"ended_epoch":%s,"duration_seconds":%s}' \
        "$(rpi5_docker_evidence_token "$run_id")" \
        "$(rpi5_docker_evidence_token "$project")" \
        "$(rpi5_docker_evidence_token "$phase")" \
        "$(rpi5_docker_evidence_token "$command_id")" \
        "$(rpi5_docker_evidence_token "$outcome")" \
        "$rc" \
        "$(rpi5_docker_evidence_token "$mutation")" \
        "$(rpi5_docker_evidence_token "$reason")" \
        "$(rpi5_docker_evidence_token "$service")" \
        "$started_epoch" \
        "$ended_epoch" \
        "$duration_seconds"
}

rpi5_docker_snapshot_mutation_state() {
    local before_file="${1:?missing before snapshot}"
    local after_file="${2:?missing after snapshot}"

    if [[ ! -r "$before_file" || ! -r "$after_file" ]]; then
        printf '%s' 'unknown'
        return 0
    fi

    if cmp -s -- "$before_file" "$after_file"; then
        printf '%s' 'none'
    else
        printf '%s' 'changed'
    fi
}

rpi5_capture_command_evidence() {
    local output_file="${1:?missing evidence output}"
    local work_dir="${2:?missing work directory}"
    shift 2

    [[ -d "$work_dir" ]] || return 125
    : >>"$output_file" || return 125

    (
        local -a pipeline_status
        set +e
        cd "$work_dir" || exit 125
        "$@" 2>&1 | tee -a "$output_file"
        pipeline_status=("${PIPESTATUS[@]}")
        [[ "${pipeline_status[1]}" -eq 0 ]] || exit 125
        exit "${pipeline_status[0]}"
    )
}

rpi5_snapshot_compose_state() {
    local project_dir="${1:?missing compose project directory}"
    local output_file="${2:?missing state output}"
    local services service container_id state_line

    [[ -d "$project_dir" ]] || return 2
    services="$(
        cd "$project_dir"
        docker compose config --services
    )" || return 2

    : >"$output_file" || return 2
    while IFS= read -r service; do
        [[ -n "$service" ]] || continue
        container_id="$(
            cd "$project_dir"
            docker compose ps -aq "$service" | awk 'NF {print; exit}'
        )" || return 2

        if [[ -z "$container_id" ]]; then
            printf '%s\tMISSING\tfalse\tnone\tMISSING\n' "$service" >>"$output_file"
            continue
        fi

        local full_id running health image_id
        full_id="$(docker inspect --format '{{.Id}}' "$container_id")" || return 2
        running="$(docker inspect --format '{{.State.Running}}' "$container_id")" || return 2
        health="$(docker inspect --format '{{if .State.Health}}{{.State.Health.Status}}{{else}}none{{end}}' "$container_id")" || return 2
        image_id="$(docker inspect --format '{{.Image}}' "$container_id")" || return 2
        printf '%s\t%s\t%s\t%s\t%s\n' \
            "$service" "$full_id" "$running" "$health" "$image_id" >>"$output_file"
    done <<<"$services"
}

rpi5_docker_failure_reason_from_log() {
    local log_file="${1:?missing command log}"
    local rc="${2:?missing rc}"
    local default_reason="${3:-command-failed}"

    if [[ "$rc" == '124' || "$rc" == '137' ]]; then
        printf '%s' 'command-timeout'
        return 0
    fi

    if [[ -r "$log_file" ]] && grep -Eiq \
        'timed?[ -]?out|timeout|context deadline exceeded|wait[^[:alnum:]]+timeout' \
        "$log_file"; then
        printf '%s' 'readiness-timeout'
        return 0
    fi

    printf '%s' "$(rpi5_docker_evidence_token "$default_reason")"
}
