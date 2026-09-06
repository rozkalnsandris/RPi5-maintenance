# Docker Compose update transaction

## Target flow

```text
validate config
    -> snapshot current service/container/image state
    -> pull candidate images
    -> compare immutable image identity
    -> if unchanged: NO_CHANGE
    -> reconcile with `docker compose up -d --wait`
    -> Docker/container health
    -> application/local endpoint health
    -> public endpoint health
    -> classify
```

## Important rules

- `docker compose pull` is the candidate acquisition phase; it does not by itself prove runtime change.
- `docker compose config -q` is used as a preflight syntax/model validation gate.
- `docker compose up -d --wait` is useful for Compose-level convergence, but it does not replace application health checks. A container without a meaningful healthcheck can be merely `running`.
- `--wait-timeout` is configurable per stack. Do not bake in an unexplained universal timeout.
- `--parallel 1` is an optional resource-control knob, not a presumed fix. Enable it only from evidence that parallel image work creates pressure or instability.
- Ordinary Compose has no Swarm-style native rollback transaction. A rollback must restore explicitly recorded known-good image/config identity and then verify.
- Never use `docker compose down`, `down -v`, image pruning or volume deletion as a generic automated repair.

## Main/CV independence

A main-stack failure does not automatically mean the CV stack must abort. Continuation requires a failure-domain gate: Docker daemon healthy, storage/network prerequisites healthy, prior stack stable or recovered, no shared prerequisite left inconsistent, and no explicit dependency on the failed component.

If shared infrastructure is suspect, stop subsequent Docker mutations.
