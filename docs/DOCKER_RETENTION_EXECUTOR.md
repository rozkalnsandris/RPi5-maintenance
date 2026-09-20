# Docker retention exact-image executor

## Status

Phase 4 source/design for issue #11. Production is unchanged.

`ops/bin/rpi5-docker-retention-executor` is not installed, not called by the weekly updater, and not scheduled. Dry-run is the default. The `--apply` path is a future LIVE mutation path that requires a separately reviewed deployment and explicit owner authorization before use.

## Inputs and review binding

The executor accepts only a planner result with schema `rpi5-docker-retention-plan-result.v1` plus one or more explicit full `sha256:` IDs supplied with `--delete-id`.

The reviewed planner-result bytes are bound with mandatory `--expected-plan-sha256`. A hash mismatch is a hard refusal.

Before any apply-side mutation, the executor re-runs the existing timeout-bounded read-only collector, Phase 2 adapter and Phase 1 planner against current runtime state. The deletion-safety view — services, protected identities, blocked lineages, per-image decisions and `delete_ids` — must match the reviewed plan. This is the Phase 4 stale-plan definition: if current safety-relevant state differs, the reviewed plan is stale and execution stops.

Capacity/report-only fields such as root usage, build-cache usage and volumes are intentionally excluded from the safety fingerprint because they do not grant image-deletion authority.

## Immediate pre-delete revalidation

For every requested ID the apply path re-runs fresh planning immediately before that image would be removed.

The target must still:

- be present in fresh `delete_ids`;
- have `action=delete` and `role=superseded`;
- have zero container references;
- map to exactly the same single managed lineage;
- have exactly the same repository ownership;
- remain outside current, candidate and previous-known-good protection.

The entire service protection set must remain equal to the reviewed plan. Any current/candidate/previous-known-good drift is a refusal.

The executor then performs an exact `docker image inspect <sha256:...>` and rejects cross-repository ownership. More than one `RepoTag` is also rejected rather than using force removal.

## Future delete command

The only image-removal argv emitted by this source is:

```text
docker image rm --no-prune sha256:<64 lowercase hex>
```

`--no-prune` prevents collateral deletion of untagged parent images. `--force` is never used. Repository/tag wildcards are never used.

Docker documents that ID-based removal can conflict when multiple tags reference an image and that force removal can untag all references to an ID. Phase 4 intentionally treats that condition as fail-closed instead of widening deletion authority.

The executor does not contain `docker system prune`, broad image prune, volume prune, container prune or network prune paths.

## Apply evidence and fail-closed semantics

`--apply` additionally requires an absolute `--evidence-output` path in an existing non-symlink directory. The evidence file is created exclusively with mode `0600` and persisted with `fsync`.

Creating that apply evidence file is the first apply-side filesystem mutation. From that point onward any timeout, Docker error, runtime/protection drift, evidence failure, ambiguous ownership or post-delete verification failure stops execution.

Per-image JSONL evidence records:

- reviewed plan SHA256;
- fresh safety fingerprint;
- explicit requested IDs;
- exact pre-delete image ID, lineage, tags and digests;
- exact delete argv;
- command result;
- post-delete verification outcome;
- `retry_attempted=false`;
- `rollback_attempted=false`.

There is no automatic retry, rollback, cleanup, alternate delete path, reboot, service restart or Compose mutation.

## Post-delete verification

After a successful remove command, the executor performs a read-only full image-ID listing and requires the exact target ID to be absent. Failure to prove absence is fail-closed.

## Activation boundary

Merging Phase 4 source does not authorize deployment or deletion.

A future production step must separately review and authorize:

1. exact source/release identity to install;
2. exact installed path and permissions;
3. reviewed planner-result artifact and SHA256;
4. exact explicit image IDs;
5. exact Compose/evidence inputs used for revalidation;
6. exact apply evidence path;
7. rollback semantics, which are deliberately **no automatic rollback** after a delete;
8. whether any build-cache policy is in scope (not part of Phase 4).

Any actual `docker image rm` remains an explicit LIVE mutation.
