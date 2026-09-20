# Docker image and build-cache retention policy

## Status

Source/design implementation for issue #11. Production is unchanged.

This policy extends the existing V24 cleanup contract without weakening it. The weekly updater still forbids broad `docker system prune`, volume pruning, container pruning and blind tagged-image pruning.

The first implementation step is a pure planner at `ops/lib/rpi5-docker-retention-plan.py`. It accepts sanitized runtime inventory and emits deterministic dry-run decisions. It does not invoke Docker and has no deletion path.

Phase 2 adds a pure sanitized runtime-inventory adapter at `ops/lib/rpi5-docker-retention-inventory.py`. It transforms reviewed sanitized evidence into the planner input schema and likewise has no Docker/subprocess execution or deletion path.

## Why a separate planner is required

Docker's `docker image prune -a` removes every image that is not referenced by a container. That is too broad for this host because an unused image can still be a candidate release, previous-known-good rollback identity, or an image owned by another Compose project/repository.

Docker's build-cache pruning has narrower controls, including age filters and storage retention, but it is still a separate mutation class from image deletion.

The maintenance policy therefore treats image provenance, build cache and volumes as separate inventories.

## Read-only production evidence — 2026-09-20

Minimum-sufficient read-only evidence for #11 showed:

- root NVMe filesystem at 46% used;
- Docker reported 261 images using 32.96 GB, with 17.82 GB reclaimable;
- Docker reported 5.324 GB of build cache, with 4.313 GB reclaimable;
- 21 containers were running;
- the daemon contains both maintenance-managed Compose images and images owned by separate application repositories;
- named volumes exist across multiple projects and are persistent state, not image-cleanup candidates.

Concrete service/repository inventory is runtime evidence and is not committed here.

## Image roles

The planner distinguishes these roles before any future executor may remove an image:

- `container-referenced`: exact image ID referenced by any container, running or stopped; always protected;
- `current`: exact current image identity for a managed service; protected;
- `candidate`: locally resolved desired/candidate image identity that may be waiting for reconcile; protected;
- `previous-known-good`: exact rollback identity proven by prior successful/pre-mutation maintenance evidence; protected;
- `count-reserve`: newest additional superseded identity retained by count policy; protected;
- `young`: superseded identity younger than the retention age; protected;
- `superseded`: old, unreferenced, unprotected identity in one unambiguous managed lineage; only this role can become a future delete candidate;
- `ambiguous`: ownership or rollback evidence is incomplete/conflicting; blocked;
- `unmanaged`: image is outside maintenance-managed lineages; ignored;
- `dangling`: left to the existing bounded dangling-image cleanup path.

## Fail-closed ownership rules

A tagged image can become a delete candidate only when all of the following are true:

1. the image belongs to exactly one maintenance-managed lineage;
2. that lineage belongs to exactly one managed project/service;
3. the service has an exact container-referenced current image identity;
4. at least one exact `previous-known-good` identity is available;
5. the image is not referenced by any container;
6. the image is not current, candidate or previous-known-good;
7. the image is older than the configured retention age;
8. the image is beyond the configured per-lineage superseded count reserve.

Missing previous-known-good evidence blocks the lineage. A lineage shared across services is blocked. An image carrying tags for more than one managed lineage is blocked. Unmanaged images are never converted into maintenance deletion candidates.

## Age and count policy

The planner receives two explicit values rather than embedding hidden defaults:

- `retention_seconds`: minimum age before a superseded image can be considered;
- `superseded_keep_per_lineage`: number of newest otherwise-eligible superseded identities retained in addition to current/candidate/previous-known-good protection.

The eventual updater integration must bind these to reviewed configuration and record the exact values in dry-run evidence before any deletion.

## Disk watermark evidence

Every plan includes:

- current root filesystem used percent;
- a configured high-watermark percent;
- whether that watermark is exceeded;
- estimated bytes represented by delete candidates.

The watermark is evidence, not permission. Crossing it must never widen ownership or rollback rules.

## Build cache

Build cache is not mixed into image ownership decisions. The planner records:

- current cache bytes;
- reclaimable bytes;
- reviewed maximum bytes;
- whether the maximum is exceeded.

The current V28 updater already uses an age-bounded `docker builder prune`. Docker also exposes storage-retention controls for builder cache. A later integration PR may combine the reviewed age policy with a storage bound, but this planner PR does not change production cache pruning.

## Volumes

Volumes are report-only in this policy. The inventory must classify each volume as `named` or `anonymous` and retain project ownership when known.

The planner always returns `action=report-only` for volumes. No future image-retention executor may infer permission to delete a volume. Any volume deletion policy requires a separate issue, inventory and LIVE authorization.

## Dry-run contract

The planner input schema is `rpi5-docker-retention-plan.v1`; the output schema is `rpi5-docker-retention-plan-result.v1`.

The result contains:

- stable per-image decisions with reasons;
- blocked lineages and exact blocking reasons;
- an explicit `delete_ids` list for review by a future executor;
- estimated delete bytes;
- root disk watermark evidence;
- build-cache watermark evidence;
- report-only volume classification.

The planner exits nonzero on malformed or contradictory inventory rather than guessing.

## Phase 2 sanitized runtime-inventory adapter

The adapter input schema is `rpi5-docker-runtime-inventory.v1`. It consumes an already-sanitized, read-only snapshot and emits the planner's existing input schema.

It derives planner state from:

- global container references mapped to exact immutable image IDs, so every referenced image remains protected regardless of ownership;
- exact maintenance-managed `project` / `service` / `lineage` / `current_container` identities;
- candidate images that are already locally resolved to exact `sha256:` IDs and proven to belong to the declared lineage;
- previous-known-good rollback identities accepted only from `source=v28-compose-evidence`, `phase=pre-mutation`, `outcome=success`, with exact project/service/image identity;
- exact image creation/size/repository metadata;
- root/build-cache watermark evidence and report-only volume inventory.

Evidence from another source, phase or outcome is not promoted to rollback proof. If no accepted previous-known-good identity exists, the adapter emits an empty rollback set and the planner blocks that lineage with `missing-previous-known-good`.

The adapter rejects unknown image IDs, duplicate managed-service identities, missing current containers, current/candidate images outside the declared lineage, invalid percentages, invalid volume kinds and contradictory cache totals rather than guessing.

Phase 2 deliberately stops at **sanitized snapshot -> planner input**. It does not collect host state, invoke Docker, add an image/cache deletion executor, alter the weekly updater cleanup path, or deploy anything to production. A later reviewed step must define the timeout-bounded read-only collector that creates this sanitized snapshot from runtime commands and V28 evidence.

## Integration boundary

This PR deliberately stops before execution wiring. A later #11 integration change must separately prove how runtime inventory is built from:

- global container image references;
- exact Compose project/service identities;
- locally resolved candidate image identities;
- prior maintenance evidence for previous-known-good rollback identities;
- image repository/tag/digest metadata;
- root filesystem and build-cache watermarks;
- volume inventory.

Only after that integration is reviewed may the updater execute exact image-ID deletion, and any production activation remains a separate explicit LIVE gate.

## Prohibited shortcuts

The #11 implementation must not introduce:

- `docker system prune`;
- `docker image prune -a` as a substitute for provenance planning;
- Docker volume pruning;
- container/network pruning;
- repository-name heuristics as sole proof of ownership;
- deletion based only on age or reclaimable-space estimates;
- deletion when previous-known-good evidence is missing;
- cross-project cleanup of application-owned images.
