# Docker build-cache storage-bound policy

## Status

Phase 5 source/design for issue #11. Production is unchanged.

The current deployed/scheduled updater is **not** changed by this phase. Phase 5 adds a deterministic policy/planner for a future separately reviewed build-cache transition. Running a prune or changing the weekly updater remains a separate explicit LIVE gate.

## Why this is separate from image retention

BuildKit cache is not rollback image ownership evidence. Cache pressure must never grant authority to delete tagged images, previous-known-good images, volumes, containers, networks, databases or application data.

The existing retention planner continues to own image classification. Phase 5 consumes only its `build_cache` evidence (`bytes`, `reclaimable_bytes`, `max_bytes`, `exceeded`) and emits a separate build-cache plan.

## Storage-bound policy

A future cache prune is planned only when all of the following are true:

1. `build_cache.bytes` exceeds the configured positive `max_bytes`;
2. the evidence is internally consistent;
3. reported reclaimable cache is nonzero and is sufficient to cover the amount above the maximum;
4. an exact Buildx builder identity is supplied;
5. the required Buildx capabilities are present.

If cache usage is within the maximum, the action is `noop`. If evidence cannot prove enough reclaimable cache to reach the bound, the action is `blocked` rather than widening deletion scope.

## Future command shape

The planner may emit this exact future argv shape:

```text
docker buildx --builder <builder> prune --force \
  --filter until=<seconds>s \
  --filter inuse=false \
  --filter shared=false \
  --max-used-space <bytes>B
```

`--force` here only suppresses the interactive confirmation prompt; it does not add cache classes. `--all` is deliberately absent, so internal/frontend records are not automatically included.

Docker documents that multiple Buildx prune filters are ANDed. `until` restricts recent cache, `inuse=false` excludes actively used records, and `shared=false` excludes records shared with other resources (typically images). `--max-used-space` makes the target storage bound explicit. Builder selection is explicit because each builder maintains its own cache.

## Read-only capability check

`ops/bin/rpi5-docker-build-cache-plan` is a read-only planner. Its runtime command allowlist is limited to:

- `docker buildx --help`;
- `docker buildx prune --help`;
- `docker buildx inspect <exact-builder>` without `--bootstrap`.

It refuses every other command, including an actual prune. A prune-required result is emitted only after proving `--builder`, `--filter`, `--force`, and `--max-used-space` support and confirming the named builder can be inspected.

## Boundaries

Phase 5 does not:

- execute `docker buildx prune` or `docker builder prune`;
- change `ops/bin/rpi5-update`;
- change timers/systemd/configuration;
- deploy the planner;
- use `--all`;
- invoke `docker system prune`;
- prune images, volumes, containers or networks;
- use build-cache pressure to widen image-retention ownership.

Any future updater wiring must separately review exact source/release identity, builder identity, cache limits, command capabilities, mutation evidence, failure semantics and health gates before an explicit LIVE authorization.

## Upstream semantics

The policy is based on Docker's current Buildx CLI contract:

- `docker buildx prune` supports `--filter`, `--max-used-space`, `--min-free-space`, `--reserved-space`, and `--all`;
- multiple different filters are combined with AND semantics;
- cache is builder-specific and an explicit builder may be selected with `--builder`.

References:

- https://docs.docker.com/reference/cli/docker/buildx/prune/
- https://docs.docker.com/build/builders/
