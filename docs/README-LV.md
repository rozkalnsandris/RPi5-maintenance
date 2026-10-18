# RPi5-maintenance — vienkāršais modelis

Repository satur **vienu nedēļas updater**, **vienu ikdienas monitoru**,
Telegram paziņotāju un systemd vienības.

Svētdien 02:20: APT → Docker/DNS gatavība → tikai galvenā Compose
`/home/andris/docker` image pull/up → šaura tīrīšana → monitors
→ reboot tikai vajadzības gadījumā pēc veiksmīgas apkopes.

Katru dienu 09:00: Docker, SSH, Cloudflared, galvenā Compose servisu
darbība/health un root diska slieksnis.

Backup wrapper/core saglabāts kopīgā lock dēļ. Atsevišķu aplikāciju
deploy, Hermes update un publiskos URL maintenance automātiski nepārvalda.
Uptime Kuma uzrauga publiskos endpointus.

Repo tīrīšana izņem **novecojušo source**, nevis RPi5 instalētos failus
vai Git vēsturi. MERGE un LIVE ir atsevišķi owner apstiprinājumi.


## Telegram paziņojumi svētdienas apkopei

Nedēļas updater atkal sūta atsevišķu īsu sākuma paziņojumu un detalizētu
veiksmes atskaiti, izmantojot to pašu izolēto Telegram notifier.
Atskaite ir piesaistīta precīzam systemd invocation ID, satur tikai
sanitizētus APT izpildes, galvenā Compose image ID izmaiņu, tīrīšanas,
monitoringa un reboot *plāna* rezultātus, nevis neapstrādātus žurnālus.
Neveiksmes un ikdienas monitora paziņojumi paliek iepriekšējā formātā.

CV, publisko URL un Hermes veselība netiek pārbaudīta šajā vienkāršajā
apkopes modelī; to veiksmīgumu Telegram atskaite neapgalvo. Hermes paliek
manuāls; rclone pārvalda APT. Sākuma paziņojuma piegāde neaptur apkopes
posmus, ja Telegram nav pieejams. Atskaite neatgriež veco doctor vai
post-reboot automatizācijas shēmu. Mainot RPi5 instalētos skriptus
un scheduled behavior, nepieciešama atsevišķa LIVE autorizācija.
