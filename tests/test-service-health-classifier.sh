#!/usr/bin/env bash
set -Eeuo pipefail
IFS=$'\n\t'

repo="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd -P)"
# shellcheck source=../ops/lib/rpi5-service-health.sh
source "$repo/ops/lib/rpi5-service-health.sh"

assert_class() {
    local expected="$1"; shift
    rpi5_service_health_classify "$@"
    [[ "$RPI5_HEALTH_CLASS" == "$expected" ]] || {
        printf 'expected=%s actual=%s reason=%s\n' "$expected" "$RPI5_HEALTH_CLASS" "$RPI5_HEALTH_REASON" >&2
        exit 1
    }
}

assert_class PASS required running required none running healthy 600 180 2
assert_class TRANSIENT required running required none running starting 30 180 2
assert_class FAIL_PERSISTENT required running required none running starting 180 180 2
assert_class FAIL_PERSISTENT required running required none running unhealthy 600 180 2
assert_class FAIL_PERSISTENT required running absent http exited none 600 120 1
assert_class TRANSIENT required running absent http running none 30 120 1
assert_class FAIL_PERSISTENT required running absent http running none 120 120 1
assert_class PASS required running absent http running none 120 120 0
assert_class FAIL_PERSISTENT required running absent http running none 120 120 2
assert_class OBSERVE observe running required none running unhealthy 600 300 2
assert_class OBSERVE observe running required none missing none 600 300 2
assert_class OBSERVE required running absent exception running none 600 300 2
assert_class FAIL_PERSISTENT required running absent none running none 600 120 2

[[ "$RPI5_HEALTH_REASON" == "no-application-proof" ]]
printf '%s\n' 'Service health classifier tests: PASS'
