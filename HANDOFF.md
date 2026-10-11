# Current handoff

## Canonical ownership

GitHub is canonical for repository source, policies, PRs, CI and continuity.
The live RPi5 is canonical for installed files, packages, Docker, systemd,
endpoints, locks and reboot requirement. Always refresh mutable states.

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

Observe the next *naturally scheduled* weekly run on 2026-10-18 using only
read-only job, Docker/DNS/health, package and reboot evidence. Confirm whether
the post-APT readiness fix prevented a repeat; do not infer success from
`--check`, a passed CI job, or an already healthy host. Do not start the weekly
updater manually as part of the audit.

No new LIVE mutation or authorization was used by this read-only audit.
Changing repository source/this handoff requires normal PR review and an
explicit MERGE decision; merge never authorizes host mutation.
