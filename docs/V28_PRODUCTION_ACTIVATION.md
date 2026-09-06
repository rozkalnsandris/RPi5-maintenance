# V28 / 0.2.0 production activation gate

## Purpose

Release `0.2.0` is published but is not production-authorized. The production gate uses a version-specific operator so deployment cannot silently follow moving `main`.

## Target identity

The operator is hard-bound to tag `0.2.0` and commit `7a5685908e06cc35aa4bb623dd9fa6a3081c4416`. It verifies the updater, Compose-policy and Docker-evidence helper by both SHA256 and Git blob identity, verifies public GitHub release metadata, and requires a successful `validate` push run for the exact release commit.

The remote tag and current operator checkout are checked with `git ls-remote`; preflight does not fetch or rewrite Git refs.

## Modes

### `--preflight`

Root read-only gate. It verifies exact release identity, current operator checkout, unchanged helper bytes, predecessor identity, timer/service state and maintenance lock availability. It emits `MUTATION_PERFORMED=false` and exits before `mutation_started=true`.

### `--apply`

Requires separate explicit LIVE authorization. The reviewed mutation order is:

1. preserve before-state in a root-only evidence directory;
2. stage exact release Compose-policy, Docker-evidence helper and updater beside their destinations;
3. atomically install the two V28 helper files;
4. run the staged updater `--check` and prove APT lists were not refreshed/changed;
5. reacquire updater-private locking and prove the live predecessor did not drift;
6. atomically replace the updater;
7. verify exact hashes/modes and unchanged timer/backup boundaries.

No `systemctl` mutation, Docker mutation, APT mutation, cleanup or reboot is part of this operator. The historical `rpi5-update.service=failed` state is not reset by activation.

## Failure semantics

Once the first host write begins, any failure preserves the before-state and staging evidence and stops. The operator performs no automatic retry, rollback, cleanup, reboot or alternate mutation. A later recovery/rollback requires a new explicit authorization based on the preserved state.

## Expected predecessor

The intended production predecessor is exact V27 updater SHA256 `f9c83acdd72131d6b696900972aa11d24978645b931846ff4ea8e6a8ed80bdc2`, with the reviewed V27 Compose-policy SHA256 `bc11a4f487efd791e23dc48f325e1aa396da14b67fc6e7429e300545ce954516` and no Docker-evidence helper. Any other root-observed predecessor fails before mutation.
