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

Repository-only regression checks now assert that the simple monitor
does not become a global degraded-state gate and that the updater's actual
ERR handler stops after a synthetic cleanup failure. The latter models
a failed operation; it is not a proof of recovery from a real `/tmp`
ENOSPC incident or host deployment.
