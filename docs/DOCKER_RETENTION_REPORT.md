# Docker retention read-only report

## Scope

This document defines Phase 3 of issue #11. Production is unchanged.

`ops/bin/rpi5-docker-retention-report` is a standalone, timeout-bounded read-only collector that feeds the Phase 2 sanitized inventory adapter and the Phase 1 retention planner. It emits either the sanitized runtime inventory (`--raw-inventory`) or the final dry-run retention plan. It has no image/cache deletion path and is not wired into the weekly updater.

## Allowed runtime reads

The command allowlist is intentionally narrow:

- `docker ps -aq`;
- `docker inspect` for the returned containers;
- `docker image ls --no-trunc --quiet` and `docker image inspect`;
- `docker compose config --format json` and `docker compose ps -q SERVICE` in exactly the reviewed `main` and `cv` project directories;
- `docker volume ls -q` and `docker volume inspect`;
- `docker system df --format '{{json .}}'`;
- `df -P /`.

Any command outside that allowlist is rejected before execution. Every subprocess has a bounded timeout. The collector never invokes pull, build, tag, prune, remove, up/down, recreate, restart, stop, start, network mutation, volume mutation, or filesystem cleanup.

## Explicit policy inputs

The report does not hide retention or pressure policy defaults. The caller must provide:

- `--retention-seconds`;
- `--superseded-keep-per-lineage`;
- `--disk-high-watermark-percent`;
- `--build-cache-max-bytes`.

The caller must also provide exactly two Compose roots using `--project main=/...` and `--project cv=/...`.

## Rollback evidence trust

At least one `--trusted-evidence-run YYYYMMDD_HHMMSS` is required. The collector never scans arbitrary historical runs and never treats a mutable image tag as rollback proof.

For each explicitly trusted run it accepts a previous-known-good image only when all of the following hold:

1. the evidence run directory is present and is not a symlink;
2. every parsed `phases.jsonl` entry carries the exact trusted run ID;
3. the project has `reconcile / compose-up / succeeded / rc=0` evidence;
4. the project has `final-health / compose-runtime-check / healthy / rc=0` evidence;
5. the run's `docker-<project>-images-before.tsv` contains the exact current Compose image reference and an immutable `sha256:` image ID;
6. that image ID still exists locally and differs from the current running image.

The newest explicitly trusted qualifying run is used for each service. Missing or non-qualifying rollback evidence is not guessed; the downstream planner blocks that lineage with `missing-previous-known-good`.

## Managed and unmanaged services

Registry-backed services in the reviewed `main` and `cv` Compose configurations become managed lineages only when exactly one running service container exists and the configured image reference resolves to an already-local immutable candidate image ID.

Buildable/local services are not promoted into maintenance-managed retention lineages. Their live containers are still part of the global container inventory, so their current image IDs remain protected. Application-owned historical images remain unmanaged unless exact reviewed provenance proves otherwise.

## Volume classification

Volumes are report-only. Docker does not persist a first-class anonymous/named creation flag, so the collector classifies an unlabeled 64-hex engine-style volume name as `anonymous`; all other volumes are `named`. This classification grants no deletion authority.

## Integration boundary

Phase 3 ends at read-only runtime collection -> sanitized adapter -> dry-run plan. It does not:

- change `rpi5-update` or its cleanup execution path;
- deploy this collector to the host;
- delete images or build cache;
- prune volumes, containers or networks;
- convert planner `delete_ids` into executable mutations.

A future exact-image-ID executor requires a separate reviewed source change, fail-closed revalidation immediately before deletion, and separate explicit LIVE authorization for production activation or cleanup.
