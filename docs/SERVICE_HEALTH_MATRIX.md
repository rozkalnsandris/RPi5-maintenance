# Service health matrix

Issue: #12.

`ops/config/service-health.tsv` is the canonical machine-readable health ownership policy. The matrix is intentionally separate from live Docker configuration: it defines what evidence maintenance must consume, not authority to mutate service Compose files.

## Policy semantics

Each service has an explicit owner, lifecycle, expected container state, Docker-health expectation, application probe or justified exception, startup grace, retry budget and enforcement classification.

`classification=required` means a failed gate is maintenance-blocking when the service is in scope. `classification=observe` means maintenance records the result but does not convert another repository's service failure or a preview workload into maintenance mutation authority.

A container with no Docker `HEALTHCHECK` is never considered application-healthy merely because Docker reports `running`. It must have an HTTP/TCP/application probe or an explicit visible exception. Exceptions are debt, not PASS-by-default.

## Startup and failure model

The next monitor integration phase must classify health as:

- `PASS`: required state and required Docker/application gate passed;
- `TRANSIENT`: service is inside its declared startup grace and has not exhausted retry budget;
- `FAIL_PERSISTENT`: missing/exited/unhealthy, probe timeout/failure after grace/retries, or required evidence unavailable;
- `OBSERVE`: external-owner or preview finding that is reported without granting maintenance mutation authority.

`starting` is therefore not silently accepted and not immediately treated as a persistent outage. Once startup grace or retries are exhausted it becomes `FAIL_PERSISTENT`.

Infrastructure failure such as Docker inventory failure or `/tmp` exhaustion is a separate fail-closed class: the monitor must not reinterpret missing health evidence as a clean application state.

## Current runtime snapshot

The 2026-09-20 read-only inventory found 21 running containers. `tests/fixtures/service-health/runtime-containers-2026-09-20.txt` records only their names as a sanitized coverage fixture; every name must map to exactly one policy row.

Two Hermes Deals `ui-dev-9190` containers are explicitly `preview`, not production gates. `rozkalns-weather-public-weather-1` is production but owned by `rozkalns_weather`; maintenance may observe its Docker health but must not redefine or mutate its service health policy.

## Convergence contract

Maintenance Docker convergence must consume this same ownership model rather than creating a second implicit list of what `running` means. `docker compose up -d --wait` remains a convergence mechanism, not sufficient application-health proof for services without meaningful healthchecks.

The source policy does not deploy healthchecks, restart containers, recreate services, change ingress or alter systemd. Any live activation of monitor/policy files or service-level healthcheck change is a separate LIVE gate.
