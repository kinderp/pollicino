# UC-297 — Smartphone companion: l'app relay BLE funziona davvero a schermo bloccato?

**Stato:** proposta documentale del **9 novembre 2026**. Nessuna implementazione o prova fisica eseguita. **Difficoltà:** medio-alta/alta per differenze Android/iOS, gestione stato e permessi. Il PHY LoRa congelato, MAC, firmware e driver restano invariati.

## Problema e scenario nella provincia di Messina

Uno studente partecipa volontariamente a una prova fra due checkpoint a Rometta e Venetico: la **scheda LoRa** conserva capsule e un **telefono di laboratorio** ne sincronizza i metadati via BLE quando possibile. In primo piano il telefono vede un contatto; con schermo bloccato o app sospesa potrebbe perdere il momento utile o completare solo parte del trasferimento. Non si può attribuire la mancata consegna a LoRa se il collo di bottiglia è il sistema operativo, la permission BLE o lo stato dell'app.

**Story:** «Come docente voglio sapere se un telefono può davvero fare da companion affidabile al relay, e quando serve aprire volontariamente l'app o usare un gateway fisso, senza promettere un servizio continuo a mia insaputa».

## Attori, nodi, valore di PollicinoNet

Quattro schede LoRa, due smartphone **forniti dalla scuola** (Android/iOS dove disponibili), due PC di checkpoint, 4–6 relay volontari, docente osservatore. Il telefono **non trasmette LoRa** salvo hardware specifico non assunto: comunica con scheda/gateway via **BLE/USB/Wi-Fi**. La scheda conserva il proprio backlog finché la sincronizzazione consentita avviene; il negoziato con il telefono è una fase distinta dal collegamento radio.

**LoRa:** annunci/capsule già supportati dalle schede e dal relativo adapter; **BLE:** companion discovery e sincronizzazione di oggetti brevi se i dispositivi supportano il bearer; **Wi-Fi/LAN/Internet:** contenuti più grandi e log; **USB/trasporto fisico:** fallback supervisionato per recuperare lo stato. Prima delle prove verificare il modello reale delle schede: non tutte le schede LoRa offrono BLE o Wi-Fi. Un gateway intermedio può esporre BLE, senza modificare il PHY.

## Stati ed evidenze proposti

`CompanionSession = {run_id, phone_os_version, device_class, radio_adapter_version, app_state: FOREGROUND|BACKGROUND|SUSPENDED|TERMINATED, permission_state, power_policy, consent_active, contact_window_id, board_queue_before?, board_queue_after?, app_receipt?, evidence_quality}`.

Registrare soltanto dati di laboratorio e versioni tecniche, mai MAC permanenti, ID del telefono privato, coordinate GPS, scansioni di sconosciuti o tracce di movimento. Distinguere `BOARD_RECEIVED`, `COMPANION_DISCOVERED`, `SYNC_STARTED`, `APP_ACCEPTED` e `UNKNOWN`. Quando mancano log, non assumere la causa né completamento.

Le politiche di background non sono uguali fra sistemi/versioni. Fonti ufficiali da verificare per versione e capability:
- Android Developers, **Communicate in the background**: https://developer.android.com/develop/connectivity/bluetooth/ble/background
- Apple Developer, **Core Bluetooth Background Processing for iOS Apps**: https://developer.apple.com/library/archive/documentation/NetworkingInternetWeb/Conceptual/CoreBluetooth_concepts/CoreBluetoothBackgroundProcessingForIOSApps/PerformingTasksWhileYourAppIsInTheBackground.html

Non dedurre da questi documenti che una specifica versione/app funzionerà senza misura; le autorizzazioni e i limiti di esecuzione restano da provare su hardware.

## Software subito, senza smartphone reali

1. Modello a eventi di **4 contatti**, 2 stati di app e 3 policy di power-management artificiali. Testare foreground, lock-screen, sospensione, terminazione, revoca permessi e riavvio.
2. LoRa registra una ricezione reale **solo nella simulazione dichiarata**; il telefono può non osservare la finestra BLE. Separare consegna alla scheda da consegna alla app.
3. Confrontare tentativi in background contro strategia user-triggered «apri l'app vicino al checkpoint» e fallback gateway PC/USB; usare le stesse finestre simulate.
4. Verificare che sessioni interrotte riprendano da uno stato persistito e che i duplicati non creino consegne applicative doppie; un permesso negato non deve essere aggirato.
5. Metriche soltanto `SIMULATED`: contatti disponibili, sync effettivi, errori noti/sconosciuti, bytes e tempo alla ricevuta, consumo **stimato non misurato**, numero di permessi richiesti.

**Accettazione:** nessun contatto perso dal companion è classificato automaticamente come perdita radio; stop e revoche rispettati, nessuna raccolta di identificativi personali e nessuna promessa di background continuo. Test non eseguiti.

## Campagna hardware minima

Due telefoni scolastici con OS e configurazione dichiarati, quattro schede LoRa, almeno un PC per log indipendenti. In laboratorio, ripetere contatti BLE controllati con app in foreground, dopo blocco schermo, in background e dopo terminazione consentita dal sistema; farlo **solo su dispositivi di prova** e annotare differenze di sistema operativo, configurazione batteria, permessi e tempi. Dopo il gate passare ai checkpoint autorizzati: relays studenteschi solo opt-in, senza richiesta di portare telefoni personali o di mantenere app sempre attive. Misurare invio, RX scheda, sessione BLE, byte e ricevuta applicativa, non inventare disponibilità o autonomia.

## Privacy, sicurezza e anti-duplicazione

No BYOD obbligatorio, no localizzazione, no scansioni continue di terzi, nessun accesso a contatti o rubrica; interruttore STOP (UC-217), identificativi effimeri per run, pairing autorizzato, autenticazione del gateway e cifratura per oggetti privati. Un telefono non autorizzato non diventa automaticamente un nodo affidabile.

**UC-033** copre il bootstrap sicuro del bearer ricco, **UC-212** l'anti-flapping, **UC-252** l'autonomia energetica del relay, **UC-268** il rendezvous LoRa e **UC-277** la localizzazione delle perdite radio→host. **UC-297 verifica uno specifico gate di prodotto: le restrizioni dell'app companion su smartphone reali e la conseguente affidabilità del servizio store-and-forward.**