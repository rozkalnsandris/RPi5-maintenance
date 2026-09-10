# `/tmp` exhaustion prevention

## Incident

On 2026-09-10 the production RPi5 `rpi5-monitor.service` failed because the host `/tmp` tmpfs reached 100% of its 2 GiB limit. Docker containers remained running, but multiple Docker health checks failed with `OCI runtime exec failed: ... no space left on device` because `runc` could not create temporary process state.

The root NVMe filesystem was not full. Read-only evidence showed `/tmp` was the dedicated RAM-backed filesystem from this exact `/etc/fstab` entry:

```text
tmpfs /tmp tmpfs defaults,strictatime,nosuid,nodev,mode=1777,size=50% 0 0
```

Large development/agent scratch directories had accumulated under `/tmp`. The immediate recovery quarantined only the explicitly authorized large directories to `/var/tmp`; it did not delete data, restart services, or reboot.

## Decision

For this RPi5, `/tmp` will return to a normal directory on the NVMe-backed root filesystem instead of increasing the tmpfs limit.

Reasons:

- Debian 13 documents that `/tmp` is tmpfs by default, normally capped at up to 50% of RAM, warns that large temporary files can exhaust it, and explicitly documents returning `/tmp` to a regular directory by masking `tmp.mount` and rebooting.
- This host intentionally runs development/agent workloads that can create multi-hundred-megabyte scratch trees. A larger tmpfs would only move the failure boundary while consuming more RAM/swap on a 4 GiB RPi5.
- FHS defines `/tmp` as disposable temporary storage and `/var/tmp` as the more persistent temporary hierarchy. Large or longer-lived scratch should prefer `/var/tmp`.
- The root NVMe has a much larger capacity margin than the 2 GiB tmpfs. The host remains protected from indefinite accumulation by a scoped `systemd-tmpfiles` policy for `/tmp` with the repository-default 14-day retention.

## Reviewed persistent state

`ops/bin/rpi5-tmp-policy-activate` is the only activation operator for this change. It is deliberately two-stage:

1. `--preflight` is read-only and accepts only the exact current legacy state.
2. `--apply` writes persistent boot policy only:
   - comments the exact known `/tmp` tmpfs line in `/etc/fstab`;
   - installs `/etc/tmpfiles.d/tmp.conf` with `D /tmp 1777 root root 14d`;
   - masks `tmp.mount` with `/etc/systemd/system/tmp.mount -> /dev/null`;
   - preserves the pre-change `/etc/fstab` in a root-only state directory.
3. `--apply` never unmounts/remounts `/tmp`, restarts services, runs cleanup, or reboots. The already-mounted tmpfs remains active until a separately authorized reboot.
4. After reboot, `--verify` is read-only and requires `/tmp` to resolve to the root disk filesystem with mode `1777` and the exact persistent policy still installed.

Any error after the first host write is fail-closed: preserve evidence and STOP. There is no automatic retry, rollback, cleanup, unmount, restart, or reboot.

## Cleanup semantics

The local `tmp.conf` intentionally overrides the vendor `/tmp` tmpfiles rule. `systemd-tmpfiles --clean` only age-cleans entries that have an age configured; this policy sets 14 days for the explicit `/tmp` scope. The `D` directive also preserves normal temporary-directory boot semantics.

This is not authorization to run cleanup manually. Normal `systemd-tmpfiles-clean.timer` behavior may apply the reviewed policy after installation according to systemd scheduling; changing that timer or manually forcing cleanup is a separate LIVE mutation.

## Scratch placement

New large or longer-lived agent/build/test scratch should use `/var/tmp` rather than `/tmp` whenever practical. This is defense in depth, not the primary safety boundary: the disk-backed `/tmp` layout prevents one development session from exhausting a small RAM-backed filesystem shared with Docker health-check execution.

## Rollback model

No rollback is automatic. Before reboot, a separately authorized rollback can restore the preserved `fstab.before` and remove only the two policy artifacts created by this operator. After reboot, rollback additionally requires an explicitly authorized reboot/cutover plan. The preserved state directory is evidence and must not be cleaned up as part of a failed apply.

## References

- Debian 13 release notes, `/tmp` tmpfs change and regular-directory rollback: https://www.debian.org/releases/stable/release-notes/issues.html
- Filesystem Hierarchy Standard, `/tmp`: https://specifications.freedesktop.org/fhs/latest/tmp.html
- Filesystem Hierarchy Standard, `/var/tmp`: https://specifications.freedesktop.org/fhs/latest/varTmp.html
- systemd tmpfiles documentation: https://www.freedesktop.org/software/systemd/man/systemd-tmpfiles.html
