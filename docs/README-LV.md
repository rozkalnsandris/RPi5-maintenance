# rpi5-maintenance — vienkāršais modelis

Šis repo vairs nav atsevišķs sarežģīts “maintenance control-plane”. Tas ir mazs RPi5 auto-update un monitor komplekts.

## Weekly update

Svētdien 02:20 `systemd` palaiž vienu `rpi5-update` skriptu:

1. APT update + konservatīvs upgrade bez pakotņu izņemšanas;
2. `/home/andris/docker` image pull + `docker compose up`;
3. 14 dienu APT/journal/dangling-image cleanup;
4. BuildKit cache tiek turēts zem konfigurēta limita;
5. tiek palaists `rpi5-monitor`;
6. reboot tikai tad, ja `/run/reboot-required` to prasa.

CV, Weather, Coloring Pages un citu app-specific simple-deployer topoloģiju weekly updater vairs nemēģina atklāt vai pārvaldīt.

## Daily monitor

Katru dienu 09:00 viens īss skripts pārbauda:

- `docker`, `ssh`, `cloudflared`;
- vai visi `/home/andris/docker` Compose servisi ir `running`;
- vai nav `unhealthy`/`restarting` konteineru;
- vai root disks nav pārsniedzis slieksni.

Publiskās lapas jau pārbauda Uptime Kuma, tāpēc monitorā nav otra URL saraksta un nav `service-health.tsv` matricas.

## Ko izmetam no aktīvās plūsmas

- Docker retention planner/inventory/executor;
- `docker system df` report pipeline;
- health classifier/grace/TSV sistēmu;
- īpašu CV Compose topoloģijas modelēšanu maintenance skriptā;
- updater-specifisku rclone/Hermes loģiku;
- runtime doctor/auto-remediation slāni.

Mērķis: pēc iespējas mazāk koda un mazāk vietu, kur maintenance var iesprūst.
