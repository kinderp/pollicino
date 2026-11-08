# UC-294 — USB/SSD come bearer: ingresso controllato dei supporti prima di fidarsi dei file

**Stato:** proposta documentale del **8 novembre 2026**, non implementata. Nessun test eseguito, nessuna misura di campo. **Difficoltà: alta** (minacce endpoint, catena di custodia, policy, parser). Non modifica PHY LoRa congelato, MAC, driver né firmware.

## Problema reale

Un data mule autorizzato trasporta un **SSD o una chiavetta gestita dalla scuola** con dispense Raiatea, documentazione offline, repository Git, backup e un dataset AI fra Villafranca, Rometta e Venetico. Il bundle può avere un hash corretto, ma **il dispositivo USB stesso** potrebbe non essere affidabile, presentarsi come una periferica diversa da memoria, esporre filesystem rischiosi o contenere altri file non autorizzati. «SHA-256 verificato» dimostra identità dei byte, **non innocuità del supporto, dei parser o dei contenuti**.

**User story:** come responsabile del laboratorio voglio che un supporto non autorizzato o ambiguo **non venga collegato ai normali PC scolastici** e che solo un bundle esattamente previsto, dopo ingresso isolato e revisione, passi a una cache di destinazione.

## Attori e perché PollicinoNet

Docenti custodi dei supporti, host dedicato di ingresso **isolato**, relay volontario che trasporta solo custodia chiusa, computer ricevente, editore del bundle, revisore e cache P2P. PollicinoNet è adatto perché il controllo viaggia separatamente dai dati: annunci, hash di manifest, esiti di revisione e ricevute attraversano LoRa e contatti intermittenti; **i gigabyte non passano via LoRa**.

- **DISCOVERY:** annuncia un bundle autorizzato senza svelarne la lista completa di file.
- **EXACT:** manifest firmato, hash file, policy, scadenze, versione importer, provenienza, eventi di handoff e ricevute.
- **SEMANTIC:** ricerca «dataset didattico» o «lezione C» senza conferire autorizzazioni a importarlo.

## Bearer

- **LoRa:** `bundle_hint`, hash di un manifest *quando pubblicabile*, richiesta di validazione e stati compatti firmati; non USB content.
- **BLE:** presa in carico locale e ricevuta breve fra nodi autorizzati, se supportato.
- **Wi-Fi/LAN/Internet:** sincronizzazione di manifest, policy ed eventuali oggetti già approvati e controllati.
- **SSD/USB gestito e trasporto fisico:** copia cifrata del contenuto massivo; mai collegamento automatico di supporti sconosciuti a postazioni di uso normale.

## Protocollo proposto

1. **Ammissione del dispositivo:** supporto scolastico inventariato e autorizzato, custodia del trasporto verificata. Se proprietario o tipo USB ignoto: `REJECT_DEVICE`, **non provare a leggerlo su una workstation scolastica**.
2. **Ingresso su host dedicato isolato** secondo policy locale con controlli di classi USB, no autorun, limitazioni dei servizi e privilegi minimi; ove possibile collegamento in sola lettura. Una configurazione read-only *non garantisce* da sola l'assenza di compromissione.
3. **Verifica del bundle:** lista autorizzata, hash e firme del publisher, dimensioni massime, percorsi normalizzati, niente esecuzione automatica, symlink/archivi/path traversal incompatibili con la policy, limiti contro decompressioni eccessive.
4. **Decisione esplicita:** `QUARANTINED`, `VERIFIED_NOT_TRUSTED`, `REVIEW_REQUIRED`, `RELEASED_FOR_AUTHORIZED_USE`, `REVOKED`; controllo finalizzato a file, scopo e versione importer. Un file firmato ma con licenza non adatta resta bloccato.
5. **Rilascio limitato:** esportare soltanto oggetti consentiti verso una cache di destinazione, idealmente attraverso un canale controllato anziché esportare di nuovo il dispositivo. Registrare hash del manifest rilasciato e ricevuta applicativa.
6. **Gestione privacy:** non esporre cataloghi completi né metadati di interesse sensibile su LoRa; cifrare in deposito e durante trasporto fisico, gestire smarrimento e retention.

`MediaIntakeRecord = {campaign_id, declared_media_id, custody_receipt?, approved_media_class, manifest_hash, policy_epoch, importer_version, owner_authorization, contents_hashes[], verdict, reviewer, source: SIMULATED|OBSERVED, evidence_completeness}`.

**Mai affermare che questo flusso renda sicuro in assoluto un device USB sconosciuto.** Il primo esperimento riguarda manifest e macchina a stati, **non la rimozione tecnica di malware**.

## Software subito (tutto inerte)

1. Creare **16 scenari sintetici** con inventario supporti e manifest inventati: sconosciuto proprietario, tipo periferica inatteso (solo stringa simulata), firma assente, hash errato, licenza negata, revoca tardiva, zip espansiva **solo dichiarata**, nomi di percorso `../` e symlink **solo come metadati**, un bundle corretto.
2. Implementare controllore deterministico su JSON/CSV, **senza montare filesystem non fidati e senza parsare archivi reali**; verificare transizioni autorizzate e condizioni `UNKNOWN`.
3. Simulare tre cache e due portatori; cambiare l'ordine di manifest, approvazione, revoca e ricevuta; verificare che non si rilasci prima del gate e che un'approvazione precedente non scavalchi la revoca.
4. Confrontare `copy-all` ingenuo (modello logico, mai eseguito) con `managed-intake`; misurare blocchi corretti, falsi blocchi, numero di file/byte autorizzati, senza interpretare il benchmark come valutazione antivirus.
5. Test di accettazione: `REJECT_DEVICE` per supporti non autorizzati; `VERIFIED_NOT_TRUSTED` non dà accesso operativo; nessuna esecuzione; nessun file fuori allowlist importato; report `SIMULATED`, `PASS/FAIL/UNKNOWN/NOT_TESTED`.

**Nessuno di questi test è stato eseguito.**

## Hardware e prove necessarie

Due PC di laboratorio, di cui uno **dedicato all'ingresso** e gestito dal personale, due supporti scolastici noti e preparati (mai di provenienza sconosciuta), 4–6 schede LoRa per soli stati/receipt, un bundle toy costituito da file inerti. Verificare allestimento e policy del sistema prima di collegare qualsiasi supporto; niente malware, dispositivi HID malevoli, exploit USB o archivi-bomba nelle esercitazioni. Testare trasmissione LoRa di stato e successivo rilascio autorizzato via LAN/SSD, con log di *accettazione applicativa*. Non serve usare studenti come vettori di supporti fino alla validazione dei checkpoint.

## Sicurezza, privacy e anti-duplicazione

Nessun contenuto reale personale, nessuna cronologia individuale dei relay, accesso al dispositivo limitato ai responsabili, revoca di autorizzazioni per versioni/uso, cifratura dei dati e conservazione temporanea dei log. La lettura di un supporto non autorizzato è una decisione di sicurezza **prima** della verifica cryptographic del bundle.

**UC-151** introduce il supporto fisico come bearer; **UC-279** mette in quarantena specifici modelli AI *dopo* l'arrivo; **UC-180** verifica pacchetti e **UC-205** controlla autorizzazioni di dataset. **UC-294 introduce il confine di fiducia tra periferica fisica e host prima di qualsiasi import**, con ammissione del dispositivo, isolamento del processo e rilascio file-per-file.

**Riferimento esterno:** [UK NCSC — Using peripherals securely](https://www.ncsc.gov.uk/collection/device-security-guidance/policies-and-settings/using-peripherals-securely), sui rischi sia dei supporti rimovibili sia di periferiche USB che si presentano come dispositivi diversi.
