# Current handoff

## Canonical ownership

GitHub is canonical for repository source, policies, PRs, CI and continuity.
The live RPi5 is canonical for installed files, packages, Docker, systemd,
endpoints, locks and reboot requirement. Always refresh mutable states.

## Naturally scheduled weekly run — 2026-10-18 (read-only confirmation)

- At 2026-10-18 09:02 CEST, live `rpi5-update.service` had
  `Result=success`, `ExecMainStatus=0` and finished at 02:23:14 CEST.
  This is evidence from the actual scheduled run, not a `--check` simulation.
- APT: 11 upgraded, 0 installed, 0 removed. Following APT, Docker and
  registry DNS passed readiness at 02:20:57; the 2026-10-11
  `auth.docker.io` resolver failure did not recur in this run.
- Main Compose expected/running: 12/12; final monitor reported
  `PASS services=12 root=59%` at 02:23:14. Maintenance cleanup reported
  15.37 GB reclaimed. These checks are not a blanket health claim for
  unrelated services.
- Current root filesystem: 130G used / 235G, 93G available (59%);
  `dpkg --audit` empty; `/run/reboot-required` absent. No reboot
  was requested or performed by this run.
- Both timers were active: next weekly run scheduled for 2026-10-25 02:20
  CEST and next daily monitor for 2026-10-19 09:00 CEST (dated observations;
  actual wall-clock timing around DST change must be checked afresh).
- Script source/live parity was not revalidated in this observation:
  reading `/usr/local/sbin/rpi5-update` as the remote read-only user was
  permission-denied. The successful service result does not establish
  immutable deployed-script identity.
- All operator checks above were read-only. No manual updater run, interactive
  host mutation, systemd reset, Docker prune, reboot or LIVE authorization
  was performed during the investigation.

## Last read-only audit — 2026-10-11 10:25 CEST

- GitHub source snapshot: main `a790b47204a31ef61008c477109d212031c89ed0`;
  PR #77 merged and left 61 repository files, without changing active runtime code.
  Exact-main `validate` check passed at this audit.
- LIVE host: `rpi5`. All active updater, monitor, notifier/helper and five
  systemd-unit Git blobs matched GitHub. The backup wrapper, backup core and
  shared lock library also matched the retained repository source.
- Installed updater: `/usr/local/sbin/rpi5-update`, Git blob
  `c4054933c4990a34dd1ff5ca90e1588d69b2fefa` (DNS readiness fix from
  merged PR #76, installed separately with exact LIVE authorization).
- The real `rpi5-update --check` and the monitor both passed; main Compose
  expected/running = 12/12; Docker, SSH, Cloudflared, containerd and AdGuard
  responded; registry DNS resolved; root filesystem 59%, `dpkg --audit` empty
  and `/run/reboot-required` absent. No shared maintenance lock holder observed.
- On 2026-10-11 at 02:21 CEST, the scheduled updater *before this DNS fix*
  failed at `docker-pull`: host resolver timeout for `auth.docker.io` following
  APT/Docker updates. The sticky `rpi5-update.service=failed` result persists;
  it is historical, not proof of a current outage. The failure notifier unit
  reported success. No operator reset, manual retry or reboot was performed.
- Both maintenance timers remain active. The next daily monitor was scheduled
  for 2026-10-12 09:00 CEST; next weekly update for 2026-10-18 02:20 CEST.
  These are dated observations, not future-state guarantees.

## Active simple model

Weekly `rpi5-update.timer` -> conservative APT -> two consecutive bounded
Docker/DNS readiness checks -> pull/up only main Compose `/home/andris/docker`
-> narrow cleanup -> monitor -> reboot only after success and if required.

Daily `rpi5-monitor.timer` -> Docker/SSH/Cloudflared, main Compose running
services, Docker unhealthy/restarting state and root disk threshold. Telegram
notifications use a separate, credential-isolated systemd unit.

Only the five active bin files, two library files and five systemd unit files
remain in `ops/`; the backup wrapper/core/shared-lock path is intentionally
retained. Application-specific deployers and Uptime Kuma own application and
public-endpoint health, Hermes remains manual, and APT owns APT-managed rclone.
Old V21–V28 activation/doctor/evidence source stays in Git history, not in
the active maintenance tree.

## Audit backlog and unresolved risks

The audit found 24 open issues and no open PR *before this handoff update*.
The canonical broader audit index remains #10 with host ownership coordinated
through `rozkalnsandris/RPi5_main#453`. Do not treat old issue acceptance text
as an instruction to restore the retired complex maintenance framework.

- #22: GitHub main branch was `protected=false`; settings/ruleset mutation
  requires its own explicit owner decision.
- #17: host Debian 12 Bookworm LTS support visibility is incomplete;
  `debian-security-support` was not installed at audit time.
- #19: Debian `apt-daily.timer` and `apt-daily-upgrade.timer` are active
  alongside weekly maintenance; overlapping APT ownership still requires review.
- #20: backup lock/source parity is verified, not full coverage or restore
  proof. Keep the backup/restore issue open.
- #23: old failed-unit status remains visible; do not clear it without
  reviewed root-cause evidence and explicit LIVE authorization.
- #12/#15: meaningful service health and mutable Docker image freshness are
  still cross-repository ownership questions. Of 12 main Compose services,
  only one declared a healthcheck and eight use `:latest`; avoid a second
  maintenance health matrix or auto-reconcile policy.
- #37/#38/#39/#41: older P3 collector/Hermes/classifier plans remain proposed,
  not part of the approved simple scheduled runtime. Re-scope/transfer/close
  only after issue-level review, never from old roadmap text alone.

## Exact current lane / next gate

The 2026-10-18 naturally scheduled update observation is complete and PASS;
the prior post-APT Docker/DNS failure was not reproduced.

Issue #23 read-only classification (2026-10-18 09:18 CEST) is complete:
systemd was degraded due to three unrelated failed one-shots. Hermes Deals
Lidl exited 20 (one_shot_wait_source, WAIT); Hermes Deals EDEKA exited 30
(shadow_cycle_nonzero, failed owner-owned shadow run); Weather dispatch caller
exited 78 on 2026-09-30 (journal absent; cause unproven). Both rpi5 maintenance
units were successful. The effective journald Storage is volatile.

At 2026-10-18 09:27 CEST the three failed one-shots were unchanged;
neither maintenance unit was among them and reboot was not required.
Live unit configs showed that Lidl and EDEKA already have project-owned
OnFailure notifications and on-failure retries (15m / 30m).

Issue #23 remaining source lane: present a single bounded, **optional**
persistent journald drop-in candidate at config/journald-persistent.conf.example
and documented verification/rollback/ownership gates. Read-only RPi5
evidence on 2026-10-18 09:36 CEST: systemd 252, explicit
/etc/systemd/journald.conf Storage=volatile; /var/log/journal exists;
journal 76.2 MB; root 59% used, 93 GB free. Source template is not
installed and must not be installed implicitly by a merge.

Owner decision received on 2026-10-18:
`APPROVE RPi5-maintenance #23 JOURNAL-RETENTION=128M/14D SOURCE-ONLY NO-LIVE`.
The owner accepts the bounded persistent journal *policy* for future
failure evidence, not host mutation. The reviewed candidate remains
`config/journald-persistent.conf.example` (Git blob
`ce51e3e384a6c3dd153c9087751fe6ebc0d0481e`). No activation is
authorized by this approval or by a merge.

LIVE journald activation performed on `rpi5` at 2026-10-18
09:51–09:53 CEST under exact owner authorization:
`AUTHORIZE LIVE RPi5-maintenance #23 JOURNAL-PERSISTENCE
HOST=rpi5 MAIN=76906edd00ff27b578203ac25f0bcf1ebd27ffd1
SOURCE-BLOB=ce51e3e384a6c3dd153c9087751fe6ebc0d0481e
ALLOW=EXACT-PREFLIGHT+INSTALL-ONE-DROPIN+RESTART-JOURNALD+
FLUSH-ONCE+READ-ONLY-VERIFY NO-REBOOT NO-RETRY NO-ROLLBACK`.
Exact source blob verified on host before write. No drop-ins/target existed;
base `/etc/systemd/journald.conf` used `Storage=volatile`.
Installed only `/etc/systemd/journald.conf.d/80-rpi5-maintenance-evidence.conf`
with root:root 0644 and exact Git blob
`ce51e3e384a6c3dd153c9087751fe6ebc0d0481e`; configuration directory
was created root:root 0755. Restarted `systemd-journald.service`
once (active/success), ran `journalctl --flush` once (success).
Read-only verification confirmed effective `Storage=persistent`,
`SystemMaxUse=128M`, `SystemKeepFree=1G`, `SystemMaxFileSize=16M`,
`MaxRetentionSec=14day`, persistent journal files under
`/var/log/journal` (~79.7 MB total journal usage), root 59% used,
93 GB available. Both RPi5 maintenance services retained success status;
`/run/reboot-required` absent. No reboot, automatic retry, rollback,
systemd reset-failed, other host changes or deployment performed.
LIVE one-time authorization consumed. This confirms live storage now,
not survival across a future reboot.

Next #23 lane: app-owner decisions for Lidl WAIT(20), EDEKA failed
shadow(30), historical Weather exit(78), and their notification/reconciliation
contracts. Post-reboot journal persistence remains untested; do not reboot
solely to test it without a separate LIVE authorization. Keep the simple
two-timer maintenance model and do not restore retired frameworks.

Any source/handoff change needs normal PR review and explicit MERGE;
MERGE never authorizes host mutation.
