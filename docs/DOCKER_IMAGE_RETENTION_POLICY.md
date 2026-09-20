# Docker image and build-cache retention policy

## Status

Source/design implementation for issue #11. Production is unchanged.

This policy extends the existing V24 cleanup contract without weakening it. The weekly updater still forbids broad `docker system prune`, volume pruning, container pruning and blind tagged-image pruning.

Phase 1 is a pure planner at `ops/lib/rpi5-docker-retention-plan.py`. Phase 2 adds the pure sanitized runtime-inventory adapter at `ops/lib/rpi5-docker-retention-inventory.py`. Neither component invokes Docker or deletes anything.

## Why a separate planner is required

Docker's broad prune modes are too wide for this host because an unused image can still be a candidate release, previous-known-good rollback identity, or an image owned by another Compose project/repository. Build cache, image provenance and volumes remain separate inventories.

## Phase 2 sanitized inventory contract

The adapter input schema is `rpi5-docker-runtime-inventory.v1`. It accepts already-sanitized, read-only evidence and emits the planner's existing `rpi5-docker-retention-plan.v1` schema.

The adapter derives planner state from:

- **global container references**: every supplied container name is attached to its exact immutable image ID, regardless of project ownership, so any referenced image is protected;
- **managed service identity**: each maintenance-managed service requires exact `project`, `service`, `lineage` and `current_container` values;
- **candidate identity**: candidate images must already be resolved to exact local `sha256:` IDs and must belong to the declared lineage;
- **previous-known-good identity**: accepted only from evidence with `source=v28-compose-evidence`, `phase=pre-mutation`, `outcome=success`, exact project/service identity and exact image ID;
- **image metadata**: exact image IDs plus creation time, size and repository/lineage metadata;
- **root/build-cache watermarks** and **report-only volume inventory**.

Evidence from another source, phase or outcome is not promoted to rollback proof. If no accepted previous-known-good ID exists, the adapter emits an empty rollback set and the existing planner blocks that lineage with `missing-previous-known-good` rather than guessing.

The adapter also rejects unknown image IDs, duplicate managed service identities, missing current containers, current/candidate images outside the declared lineage, invalid percentages, invalid volume kinds and contradictory cache totals.

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
- `unmanaged`: image is outside maintenance-managed lineages; ignored unless globally container-referenced;
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

Missing rollback evidence, shared lineages and multi-lineage images block deletion. Unmanaged images are never converted into maintenance deletion candidates.

## Age, disk and build-cache evidence

The planner receives explicit `retention_seconds`, `superseded_keep_per_lineage`, root-used percentage, disk high-watermark percentage and build-cache totals. Watermarks are evidence only and never widen ownership rules. Build cache remains report-only in the planner; the existing V28 age-bounded cache handling is unchanged by Phase 2.

## Volumes

Volumes remain report-only and are classified as `named` or `anonymous`, with project ownership retained when known. No image-retention path may infer permission to delete a volume.

## Integration boundary

Phase 2 deliberately stops at **sanitized snapshot -> planner input**. It does not add host probes, Docker execution, image deletion, cache deletion, weekly-updater cleanup wiring or production deployment. A later reviewed step must define the timeout-bounded read-only collector that creates this sanitized snapshot from runtime commands and V28 evidence.

Only after collection/integration is reviewed may a separate exact-image-ID executor be designed. Any production activation or actual cleanup remains a separate explicit LIVE gate.

## Prohibited shortcuts

The #11 implementation must not introduce broad prune commands, Docker volume pruning, container/network pruning, repository-name heuristics as sole proof of ownership, deletion based only on age/reclaimable space, deletion without previous-known-good evidence, or cross-project cleanup of application-owned images.
