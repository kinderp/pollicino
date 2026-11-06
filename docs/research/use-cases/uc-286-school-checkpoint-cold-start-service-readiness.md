# UC-286 — Cold start del checkpoint: quanto tempo serve per tornare a consegnare?

**Stato:** proposta documentale del **6 novembre 2026**. Non implementata, nessun test software o fisico eseguito, nessun risultato radio. **Difficoltà medio-alta.** Non modificare PHY LoRa congelato, MAC, driver o firmware.

## Problema e confine del caso

Un checkpoint scolastico alimentato in bassa tensione potrebbe spegnersi per manutenzione o perdita della sua alimentazione *locale*. Dopo la riaccensione il LED può essere acceso mentre il servizio non è ancora pronto: adapter radio non disponibile, chiavi o autorizzazioni non ricaricate, coda da verificare, applicazione host non avviata o ricevute non ancora registrate. **Vogliamo misurare il tempo fino alla prima consegna applicativa esatta**, non il semplice tempo di boot o un ipotetico uptime radio. Il caso non riguarda un'interruzione della rete elettrica pubblica e non promette continuità di emergenza.

**Scenario Messina:** due checkpoint scolastici autorizzati fra Messina, Villafranca, Rometta e Venetico custodiscono capsule di prova. Il nodo Rometta viene spento e riacceso solo dal docente in laboratorio; un secondo checkpoint e, più avanti, relay volontari degli studenti trasportano annunci e ricevute in store-and-forward. Non servono GPS né tracciati di spostamento.

## Attori e perché PollicinoNet

Docente responsabile, checkpoint TX/RX, host/collector, relay studente solo nella fase successiva, eventuale ricevitore indipendente, osservatore dei log. La rete tollera disconnessioni e code differite: è essenziale distinguere **power-on**, **processo avviato**, **radio osservabile**, **servizio autenticato**, **custodia verificata**, **EXACT ricevuto** e **applicazione che lo accetta**. Nessuna fase è dedotta automaticamente da quella precedente.

## Bearer e dati

- **LoRa:** discovery e capsule artificiali già ammesse dall'adapter; non assumere supporto a una dimensione di payload o a tempi RX non verificati.
- **BLE:** configurazione/log locali e handoff, solo se già supportato.
- **Wi-Fi/LAN/Internet:** raccolta log e bulk, percorso distinto dal risultato LoRa.
- **USB/SD e trasporto fisico:** recupero dei log durante partizioni; canale di verifica indipendente.
- **DISCOVERY** = checkpoint nuovamente osservabile; **EXACT** = ID, hash e ricevuta verificata; **SEMANTIC** = classificazione controllata della causa di indisponibilità, mai inventata.

Fixture minima sintetica: `campaign_id`, `node_ephemeral_id`, `boot_epoch`, `power_cycle_requested_at`, `boot_observed_at?`, `adapter_ready_at?`, `auth_ready_at?`, `queue_recovered_at?`, `tx_confirmed_at?`, `rx_observed_at?`, `app_accepted_at?`, `log_completeness`, `source=SIMULATED|OBSERVED`. Gli eventi ignoti restano `UNKNOWN`. Conservare solo quanto necessario per il confronto.

## Esperimento software subito (da realizzare, non eseguito)

1. Simulare 6 riavvii di un checkpoint, con code artificiali, due receiver, cronologie riproducibili e riavvii ripetuti. Distinguere misure `FIRST_READY`, `FIRST_RX` e `FIRST_APP_ACCEPTED`, oltre agli oggetti che restano ancora in coda.
2. Iniettare adapter lento, ordine errato dei processi, chiave di test non disponibile, coda verificata dopo il boot, receipt duplicati, reboot durante la scrittura e log con eventi assenti. Nessun algoritmo può attribuire una causa di guasto non osservabile.
3. Confrontare due policy **applicative**: avvio immediato del trasferimento vs sblocco dopo controlli di autenticazione/custodia. Non alterare radio/firmware.
4. Calcolare tempo alla prima capsule accettata e quota di oggetti ancora recuperabili **solo sui run con timestamp attendibili**; mostrare `NOT_COMPARABLE` e `UNKNOWN` per i run incompleti.
5. Ripetere con seed fisso e confrontare output byte per byte. Tutti i risultati iniziali marcati `SIMULATED`.

**Accettazione:** (A) LED/boot senza receipt non produce `SERVICE_READY`; (B) receipt riferite all'epoch precedente non contano come consegne del nuovo run (UC-256); (C) le capsule già accettate non sono accettate due volte (UC-221/175); (D) nessun denominatore senza log TX/RX credibili (UC-178/277); (E) un power cycle non autorizza cancellazione indiscriminata delle custodie durevoli (UC-253).

## Gate fisico

**4–6 schede, due PC/collector e alimentazioni USB sicure** in un'aula autorizzata, senza toccare impianti elettrici. Verificare prima che adapter/firmware *già esistenti* espongano i marcatori necessari. Effettuare piccoli cicli manuali di spegnimento/riaccensione **del solo banco di prova**, con cronometro/log indipendenti, una capsula artificiale e una ricevuta applicativa verificata. Registrare orologi e incertezza, provenienza log, versione hardware/software, energia se misurabile, e distinguere esito host da esito radio. Se un marcatore non è osservabile, riportare `UNKNOWN` e non attribuire causa. Successiva estensione a due checkpoint scolastici e, soltanto con consenso, relay studenti senza traiettorie personali. Verificare preventivamente frequenze/potenze/airtime e regole radio applicabili.

## Privacy, sicurezza, limitazioni

Solo ID effimeri e payload fittizi, nessun dato studente, nessuna simulazione di allerta reale. Revoche e chiavi di test non devono essere eluse in nome della disponibilità; dopo riavvio non eseguire comandi scaduti. Nessuna promessa di servizio salvavita, nessuna prova con interruzioni a servizi dell'istituto. Difficoltà **medio-alta**: raccogliere una cronologia completa e confrontabile è più difficile che cronometrare il boot.

## Anti-duplicazione e riferimenti

**UC-233** studia il picco collettivo di code quando *molti* relay tornano connessi; **UC-184** salva stato prima di un brownout; **UC-253** verifica custodia dopo spegnimento; **UC-271** confronta USB/powerbank; **UC-283** sceglie posizione indoor; **UC-277** localizza perdite a valle della radio. Qui il nuovo gate è **il tempo verificato fra riaccensione di un singolo checkpoint e prima consegna applicativa utile**, con diagnosi degli stati intermedi e marcatori mancanti.

Riferimento concettuale: [RFC 9171 — Bundle Protocol v7](https://www.rfc-editor.org/rfc/rfc9171.html) descrive un modello store-carry-forward, **non è una dichiarazione che PollicinoNet implementi BPv7**.
