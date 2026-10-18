# Simple operations runbook

## When `rpi5-update.service` fails

1. Read `journalctl -u rpi5-update.service` around the failed invocation.
   Record the first `FAIL phase=...` and its stderr.
2. Check Docker, the affected Compose services and dependent DNS, as needed.
   A failed update does not by itself prove a current service outage.
3. Confirm APT/package consistency, current state, shared lock and
   `/run/reboot-required` only when the failing phase warrants it.
4. If the system is healthy but the update is incomplete, preserve the
   evidence and wait for reviewed remediation. Do not rerun mutation merely
   to clear the red systemd state.
5. Manual update runs, Docker recovery, service restarts, cleanup or reboot
   require separate explicit LIVE authorization.

`systemctl reset-failed` only clears historical unit failure state; it
does not resolve its cause and is not part of the automatic update.

## Normal ownership

- Main Compose: `/home/andris/docker`.
- Other applications and public endpoints: respective deployers/Uptime Kuma.
- Backup: separate runner protected by the shared maintenance lock.
- Hermes: independent/manual maintenance.
- Pinned GitHub source and installed RPi5 files have distinct identities.

## When systemd is `degraded` (issue #23)

A `failed` result is evidence of a **unit invocation**, not automatically a
current host/application outage. First classify the exact unit; do not blindly
restart it or reset its failed state. Use only read-only commands:

```text
systemctl list-units --state=failed --no-pager
systemctl show UNIT.service -p Type -p ActiveState -p Result -p ExecMainStatus -p ExecMainExitTimestamp -p FragmentPath -p OnFailure -p Restart
journalctl -u UNIT.service --no-pager -n 40 -o short-iso
```

For each unit record its owner, one-shot vs long-running lifecycle, timestamp,
exit/status reason, current affected service health, and whether the journal
still contains the failed invocation. Redact any credentials, URLs or personal
data before saving evidence to an issue. `/tmp` ENOSPC and other host faults
need their own causal proof, not an inference from a historical red unit.

### Scoped example: 2026-10-18 09:18 CEST

- `rpi5-update.service` succeeded at 02:23 and `rpi5-monitor.service`
  succeeded at 09:00. Neither is currently failed.
- `hermes-lidl-weekly.service` (Hermes Deals owner): one-shot,
  `exit=20` at 00:40; journal reason `one_shot_wait_source`. This is a
  **WAIT/no-source** outcome, not evidence of a crashed persistent daemon.
  It still sets systemd `failed` and has an owner-specific `OnFailure`.
- `hermes-edeka-weekly-monitor.service` (Hermes Deals owner): one-shot,
  `exit=30` at 01:10; reason `shadow_cycle_nonzero`, after retries.
  Production writes/deploy were not reported. This is a **failed shadow
  run requiring owner triage**, not proof that a production daemon is down
  and not automatically an accepted success.
- `rozkalns-weather-operator-v7-dispatch-caller.service` (Weather
  operator owner): static one-shot, `exit=78` at 2026-09-30 21:55.
  Its journal currently has no entries, so the cause is **unknown**;
  age alone is not proof the cause was fixed.
- Manager state was `degraded` because the above three units were failed.
  This does not contradict the bounded maintenance monitor's `PASS`.

The main `rpi5-monitor` intentionally checks its own host/main Compose
scope. Do **not** make it fail on every other project's historical or
intentional one-shot exit: that would duplicate project ownership and turn
expected WAIT states into generic maintenance incidents. New/changed failures
should be classified and alerted by the owning unit/project with their
timestamp and exit reason; agreeing that owner-specific contract remains
open in issue #23, not implemented by this runbook change.

### Preservation and reconciliation

The observed journald effective `Storage=volatile` (2026-10-18); journal
usage was 76.2 MB. The missing Weather invocation cannot be reconstructed
from existing journal records. Before any authorized reconciliation, capture
the available `systemctl show` metadata, exact relevant journal excerpts
and owner decision outside transient journal storage. Assess bounded
owner-specific failure evidence retention separately; changing journald
policy is **not** an automatic maintenance action.

After the **owner** confirms the actual cause is addressed or an exit is an
explicitly accepted outcome, a proposed unit/status reconciliation must name
the exact unit and expected before/after states, check conflicts and obtain
separate LIVE authorization. `systemctl reset-failed`, changing
`SuccessExitStatus=`, disabling/restarting a timer/unit or rerunning a job
are all prohibited without that permission. Do not suppress evidence simply
to make `systemctl is-system-running` say `running`.

### Owner-owned next actions, not another host monitor

The 2026-10-18 09:27 read-only unit configuration confirms both Hermes
one-shots already have `OnFailure` notifications and
`Restart=on-failure`: Lidl at 15 minutes, EDEKA at 30 minutes.
These retries explain why a WAIT/BLOCKED outcome can create repeated failed
invocations. No extra `rpi5-monitor` alert, retry or global failure scanner
is proposed.

- **Lidl owner**: decide whether `one_shot_wait_source` (20) should count
  as a handled/expected WAIT and whether a retry or failure notification
  is appropriate. Document this as an exact unit policy, not a generic
  suppression rule.
- **EDEKA owner**: investigate `shadow_cycle_nonzero` (30) using its
  existing structured run evidence, retaining the failure signal until
  the source condition and notification policy are reviewed.
- **Weather owner**: reconstruct `exit=78` using available non-journal
  release/run evidence. When no evidence survives, record the uncertainty
  and require an explicit owner decision rather than claim resolution.
- **Journal retention**: any change from effective `Storage=volatile`
  must be capacity-bounded, owned, source-reviewed and separately authorized
  for LIVE. Do not turn the weekly updater's journal vacuum into a
  general log-retention replacement.

Each owner should preserve a small, sanitized record of unit name,
invocation timestamp, exit reason/code, affected-service state and any
notifier outcome before deciding to reconcile it. Notify only on newly
observed owner-significant failures, not every time an old `failed`
status is read. Cross-project notification behavior remains an open
acceptance item in #23 until owner policies are actually delivered.

Read-only check at 2026-10-18 10:02 CEST: existing Lidl
`hermes-lidl-weekly-failure@hermes-lidl-weekly.service.service`
completed successfully at 00:55:12 and EDEKA
`hermes-edeka-weekly-monitor-failure@hermes-edeka-weekly-monitor.service.service`
completed successfully at 01:40:13, both with exit 0. The short
journals confirm invocation and successful systemd completion, **not**
that the alert reached Telegram. The two weekly timers were
active/enabled and had their next event at 2026-10-25 00:10 CEST.
The Weather dispatch caller timer was active/enabled but exposed
no next realtime elapse at that observation; its old exit 78 has
no proven cause. These belong to their respective application owners.
Avoid adding a central duplicate failed-unit alert or clearing
`failed` merely because an owner notifier ran successfully.

Repository-only regression checks now assert that the simple monitor
does not become a global degraded-state gate and that the updater's actual
ERR handler stops after a synthetic cleanup failure. The latter models
a failed operation; it is not a proof of recovery from a real `/tmp`
ENOSPC incident or host deployment.

### Source-only bounded journal persistence proposal

On 2026-10-18 09:36 CEST, RPi5 ran systemd 252 (Debian 12) with
`Storage=volatile` explicitly set in `/etc/systemd/journald.conf`.
The persistent directory `/var/log/journal` already existed, but that
does **not** override the explicit volatile setting. The journal used
76.2 MB; root had 93 GB free. There is no immediate disk emergency.

A small candidate file is checked in at
[`config/journald-persistent.conf.example`](../config/journald-persistent.conf.example).
It proposes one administrator-owned drop-in at
`/etc/systemd/journald.conf.d/80-rpi5-maintenance-evidence.conf` with:

- `Storage=persistent` to retain future journals across reboot where
  disk storage is writable;
- `SystemMaxUse=128M` and `SystemKeepFree=1G` to bound persistent
  journal disk use and leave space for other consumers;
- `SystemMaxFileSize=16M` to keep rotation granular, and
  `MaxRetentionSec=14day` as a maximum age.

These are **limits, not guarantees** of 14 days of retained history:
heavy traffic may rotate entries sooner; active files and changing disk
conditions can temporarily exceed nominal quota/retention expectations.
This change will not restore already-lost Weather failure logs.
Persistent journaling may retain sensitive messages: retain root-controlled
access and never publish full logs.

The repository itself does **not** deploy this example automatically.
The operator installed the exact reviewed bytes on `rpi5` on 2026-10-18
under a separate, one-time LIVE authorization. Any subsequent change,
restart, flush, rollback or reboot is a new LIVE mutation needing
its own authorization. A source merge does not authorize deployment.
Retention across a future reboot has not been verified.

Official Debian 12 references:
[`journald.conf(5)`](https://manpages.debian.org/bookworm/systemd/journald.conf.5.en.html)
and [`systemd.service(5)`](https://manpages.debian.org/bookworm/systemd/systemd.service.5.en.html).


### Historical LIVE activation plan and authority (2026-10-18)

Owner instruction: `APPROVE RPi5-maintenance #23 JOURNAL-RETENTION=128M/14D
SOURCE-ONLY NO-LIVE`. This approves exactly the retained-policy decision,
not installation, service changes, backfill or a reboot. Existing GitHub
candidate blob: `ce51e3e384a6c3dd153c9087751fe6ebc0d0481e`.

**Exact conditional LIVE activation plan (requires a new authorization):**

1. Target only host `rpi5` and
   `/etc/systemd/journald.conf.d/80-rpi5-maintenance-evidence.conf`.
   Refresh `main` and reviewed candidate SHA, verify the running host,
   effective `journald` configuration, all potential competing drop-ins,
   source bytes/identity, destination absence, permissions, disk headroom,
   journal health and conflict/lock state. Do not assume a GitHub merge
   installed the file or that a staging copy exists.
2. Under separate, exact LIVE authorization, install the **identical
   reviewed example bytes** as one root-owned `0644` drop-in (creating
   its `0755` configuration directory only if absent). No writes to the
   existing `/etc/systemd/journald.conf`. Immediately verify content
   identity and ownership; if verification fails, STOP.
3. Restart only `systemd-journald.service` so it reads the new
   configuration; check that it remains active. Then execute
   `journalctl --flush` once, which the Debian Bookworm
   `journald.conf(5)` page identifies as the switch from volatile
   early-boot journal storage to persistent storage. These are distinct,
   explicitly authorized mutations, not routine read-only checks.
4. Read-only verify effective `Storage=persistent`,
   `SystemMaxUse=128M`, `SystemKeepFree=1G`,
   `SystemMaxFileSize=16M`, `MaxRetentionSec=14day`; confirm
   journald service health, journal records under `/var/log/journal`,
   journal disk usage and available root space. Do not infer
   post-reboot persistence without a separately authorized reboot.

**Fail-closed and recovery:** authorization is consumed when the first
LIVE write begins. Any unexpected state, command error, timeout or drift
after that point requires minimal read-only evidence and STOP. Do not
retry, remove the drop-in, restart again, flush again, reset failed units,
reboot, or automatically roll back. An explicit future recovery
authorization must name the exact file/unit action and observed state.
No automated installer, timer, dependency or monitoring feature is added.

Debian Bookworm `journald.conf(5)` states that administrator drop-ins
override the main file, `Storage=persistent` prefers
`/var/log/journal`, and `journalctl --flush` is the supported
transition after volatile early-boot logging. A quota is a bound, not
a guarantee that all 14 days of messages survive rotation.

### Actual LIVE activation evidence — 2026-10-18 09:51–09:53 CEST

Explicit owner authorization:
`AUTHORIZE LIVE RPi5-maintenance #23 JOURNAL-PERSISTENCE HOST=rpi5
MAIN=76906edd00ff27b578203ac25f0bcf1ebd27ffd1
SOURCE-BLOB=ce51e3e384a6c3dd153c9087751fe6ebc0d0481e
ALLOW=EXACT-PREFLIGHT+INSTALL-ONE-DROPIN+RESTART-JOURNALD+
FLUSH-ONCE+READ-ONLY-VERIFY NO-REBOOT NO-RETRY NO-ROLLBACK`.

Host verified `rpi5`; fresh GitHub main and on-host input hash matched.
Prior state: explicit `Storage=volatile`, no competing drop-ins,
target absent, journald running, root at 59%, reboot not required.
Applied the reviewed drop-in once, creating only its config directory
(root:root 0755) and file (root:root 0644, Git blob
`ce51e3e384a6c3dd153c9087751fe6ebc0d0481e`).
Restarted `systemd-journald.service` **once** and executed
`journalctl --flush` **once**. Both commands succeeded.
Read-only verification: effective persistent storage and all four
reviewed capacity/retention values, active/success journald,
persistent `.journal` files under `/var/log/journal`, approximately
79.7 MB current journal usage, 93 GB root free, updater/monitor
`Result=success`, reboot not required. No restart or reboot beyond
the exact authorized journald restart; no retry, rollback, failed-unit
reset, timer or application mutation.

**Remaining limits:** 14 days is a maximum age, not a retention
guarantee; previously lost Weather logs cannot be recovered.
No actual reboot occurred, so post-reboot journal continuity remains
unverified. Further journal-policy changes or a reboot require fresh,
specific LIVE approval. Issue #23 remains open for app-owned failure
classification and reconciliation.
