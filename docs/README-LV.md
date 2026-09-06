# rpi5-maintenance — kopsavilkums latviski

Šis repo kļūst par atsevišķu RPi5 uzturēšanas vadības slāni. Tas nepieder nevienai konkrētai lietotnei; tas koordinē APT, Docker Compose atjaunināšanu, veselības pārbaudes, ierobežotu atkopšanu, reboot lēmumu, pierādījumu saglabāšanu un paziņojumus.

Galvenais princips: **update kļūda nav automātiski sistēmas kļūda**. Ja update komanda atgriež kļūdu, bet nav palikusi bīstama daļēja mutation un visi servisi ir pārbaudīti kā veseli, rezultāts var būt `RECOVERED` vai `DEGRADED`, nevis `CRITICAL`.

Hermes/log-doctor ideja tiek saglabāta, bet padarīta deterministiska: tas drīkst izpildīt tikai iepriekš definētus, ierobežotus remediation playbookus. AI nedrīkst pats izdomāt un palaist patvaļīgas root/Docker/config komandas.

Pirmajā migrācijas posmā esošais kods no `RPi5_main` tiek pārnests gandrīz 1:1 un tiek pierādīta testu/paritātes atbilstība. Tikai pēc tam atsevišķos PR tiek ieviests labāks `stderr`/evidence, `compose up --wait`, precīzāks failure modelis, stacku neatkarības noteikumi un systemd/application backoff.

Production nepāriet uz jauno repo automātiski. Production izmanto tikai konkrētu, pārbaudītu un autorizētu release/commit.
