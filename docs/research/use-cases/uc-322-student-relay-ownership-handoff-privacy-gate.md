# UC-322 — Riassegnazione sicura di una scheda relay fra due studenti

**Stato (19 novembre 2026):** proposta documentale, non implementata né provata. **Difficoltà:** medio-alta in simulazione, alta per la sanitizzazione verificabile su flash reale. Nessuna modifica a PHY LoRa congelato, MAC, firmware o driver.

## Problema, storia e nodi
Una scheda PollicinoNet prestata alla classe A viene restituita al laboratorio e poi assegnata alla classe B. La scheda potrebbe contenere capsule ancora in coda, chiavi della vecchia epoca, ricevute, pseudonimi, configurazioni e log. Un semplice «ripristino impostazioni» non dimostra che ogni copia su flash sia inaccessibile. Nemmeno possiamo cancellare la coda e sostenere che le consegne promesse siano state completate.

**Storia d'uso:** un docente deve poter riassegnare una scheda solo dopo aver trattato le consegne irrisolte e aver verificato la separazione della nuova identità dal precedente utilizzatore. Attori: scheda scolastica, amministratore docente, cache di origine e destinazione, due custodi volontari rappresentati da epoche anonime, registro delle credenziali, relay di altri studenti.

## Perché serve PollicinoNet
Con lo store-and-forward, un relay può custodire dati anche quando mittente e destinatario sono offline. Il cambio di custode è quindi una **transizione di responsabilità, dati e fiducia**, non soltanto un nuovo nome sulla scatola. Proponiamo stati locali: ACTIVE_A → HANDOVER_FROZEN → QUEUE_RECONCILED_OR_EXPLICITLY_UNRESOLVED → SANITIZATION_REVIEW → NEW_KEYS_AND_ROLE_B → ACTIVE_B. Se un gate non è verificabile: QUARANTINED, non READY.

Un handoff della coda è riuscito soltanto quando il nuovo holder autorizzato ha verificato e conservato l'oggetto intero; l'ACK della vecchia scheda non equivale alla consegna finale. La revoca di vecchie credenziali può impiegare tempo a propagarsi nella rete intermittente. Non attribuiamo capacità di cancellazione sicura al microcontrollore prima di una verifica tecnica.

## Bearer possibili
- **LoRa:** avvisi compatti e autenticati su cambio epoca, disponibilità delle ricevute o revoca, soltanto nei limiti del PHY/adapter esistenti; non trasporta dump di memoria.
- **BLE:** incontro locale supervisionato per scambio di attestazioni o richieste limitate, se disponibile sull'hardware.
- **Wi-Fi/LAN/Internet:** workstation scolastica di provisioning, verifiche di code/ciphertext, aggiornamento credenziali e ricevute quando disponibili.
- **USB/SD/trasporto fisico:** scheda fisica restituita, backup *autorizzato e cifrato* di capsule ammissibili, log di laboratorio senza dati reali degli studenti.

## Prova immediata soltanto software — proposta, non eseguita
Simulare 5 nodi, 30 capsule fittizie (pubbliche, cifrate e non trasferibili), due epoche A/B e tre politiche: riutilizzo ingenuo, cancellazione della sola coda, riassegnazione gated. Iniettare crash a metà handoff, ACK anticipato, revoca che arriva tardi, duplicati, impossibilità di verificare la sanitizzazione, vecchio token ancora in cache e oggetto non esportabile per policy.

**Invarianti PASS attesi:** nessun oggetto di A visibile a B; nessuna chiave di A riutilizzata; nessuna riassegnazione READY senza gate registrati; nessuna consegna inventata; oggetti non risolti conteggiati come UNRESOLVED; decisioni idempotenti ai replay. Metriche: riassegnazioni bloccate correttamente, esposizioni simulate, oggetti risolti/irrisolti e numero di falsi READY. Tutti i numeri sono **parametri di test**, non risultati.

## Prova su hardware e territorio
Iniziare con 4 schede scolastiche e 2 PC in laboratorio: usare soltanto dati fittizi, interrompere la procedura dopo ogni gate, controllare nuova identità, ripresa delle code e assenza di dati esposti nelle interfacce normalmente accessibili. Una pretesa di *sanitizzazione completa della flash* richiede verifiche specifiche del dispositivo/firmware e del mezzo di memoria: un controllo applicativo da solo non basta. Se non verificabile, la scheda rimane in quarantena per l'uso con dati sensibili.

Solo dopo si potranno riassegnare relay di prova in una rete volontaria con checkpoint scolastici fra Milazzo, Venetico e Rometta, senza tracciare studenti né assumere collegamenti radio intercomunali. Raccogliere ricevute applicative vere, non dedurre PDR, copertura o autonomia da simulazioni.

## Privacy, sicurezza e difficoltà
Usare epoche di custodia anonime e registri minimizzati; niente nominativi di minorenni, messaggi privati o orari personali di spostamento. La workstation deve essere autorizzata; le credenziali vengono ruotate, mai mostrate al nuovo custode. Lo schema di cancellazione segue una policy verificata per il supporto di memoria: la revoca delle chiavi non implica automaticamente distruzione fisica di ogni copia residua.

## Perché non è un duplicato
**UC-068** studia l'arruolamento iniziale; **UC-201** il ritiro e il salvataggio delle code; **UC-307** lo smarrimento improvviso; **UC-253** la durabilità dopo spegnimento. Qui il requisito nuovo è il **passaggio fra due utilizzatori con barriera di privacy e nuova epoca di fiducia**, accompagnato dal caso negativo in cui il riuso è proibito.

## Fonti di contesto, non misure PollicinoNet
- NIST SP 800-88 Rev. 2, *Guidelines for Media Sanitization*, pubblicato il 26 settembre 2025: https://csrc.nist.gov/pubs/sp/800/88/r2/final
- NIST IR 8350, *Trusted IoT Device Network-Layer Onboarding* (ciclo di vita/repurposing): https://nvlpubs.nist.gov/nistpubs/ir/2025/NIST.IR.8350.pdf
