# UC-300 — Rete messinese: rimozione controllata di un relay ponte e resilienza reale

**Stato:** proposta documentale del 10 novembre 2026. **Nessuna prova software o fisica eseguita.** Difficoltà: medio-alta per pianificazione/testbed e interpretazione; alta nell'estensione provinciale. Il PHY LoRa congelato, MAC, driver e firmware non vengono modificati.

## Problema e caso concreto

Una rete di schede trasporta capsule fra due gruppi scolastici solo grazie a un checkpoint/relay che si comporta da **ponte**. Se il relay viene spento o resta indisponibile, il traffico di una zona potrebbe non raggiungere l'altra entro la scadenza. Una mappa con un collegamento disegnato non è una dimostrazione di resilienza, e la perdita di un nodo non prova che tutta la provincia sia isolata.

**Storia:** «Come docente voglio sapere se le piccole consegne PollicinoNet arrivano quando un relay intermedio è presente e quando lo rimuovo in modo controllato, con un esperimento equo e ripetibile, senza trasformare gli studenti in infrastruttura obbligatoria».

## Attori e scenario nell'hinterland di Messina

Due gruppi di nodi sorgente/destinazione, un ponte di prova, un eventuale relay di percorso alternativo, due PC/collector indipendenti, docente e relay volontari. Simulare dapprima due isole chiamate **Rometta** e **Venetico** con checkpoint di banco; poi soltanto dopo i gate fisici utilizzare checkpoint autorizzati fra Villafranca, Rometta, Spadafora e Venetico. Nessuna ipotesi di collegamento LoRa diretto fra comuni o di disponibilità degli studenti.

PollicinoNet è naturale per la prova: custodisce i bundle, li inoltra su **contatti temporali** e rende possibile una consegna differita anche senza percorso simultaneo. Confrontiamo una rete con ponte e la stessa rete senza ponte, misurando le **ricevute applicative**, non le presunte coperture.

## Bearer

- **LoRa:** soltanto le capsule/discovery già supportate dal PHY/adattatore, nei budget radio applicabili. Non introdurre nuove modalità radio.
- **BLE:** contatti locali e acquisizione dei log quando consentiti; non assumere BLE sulle schede LoRa.
- **Wi-Fi/LAN/Internet:** upload di log e oggetti più grandi, come configurazioni di prova, quando approvati e disponibili.
- **Trasporto fisico:** passaggio volontario e schedulato del relay di prova, oppure USB/SSD autorizzati per evidenze; annotare questo bearer **separatamente** da LoRa.

## Contratto e disegno sperimentale

`BridgeTrial={trial_id,arm: BRIDGE_ON|BRIDGE_OFF|ALTERNATE,workload_hash,adapter_version,tx_schedule,paired_window_id,source_handoffs,destination_app_receipts,missing_log_flags,clock_uncertainty,volunteer_stop_flags,consumed_bearer_classes}`.

**Basi confrontabili:** stessa quantità di oggetti artificiali, stesso TTL/deadline, identiche policy di retry e budget; alternare l'ordine dei bracci in finestre accoppiate. Il braccio `BRIDGE_OFF` è la **disattivazione programmata di un dispositivo sperimentale**, non sabotaggio del servizio. Misurare a parte l'eventuale percorso alternativo. Se il trasporto via USB completa la consegna, non attribuirla a un collegamento LoRa. Se non abbiamo log completi, dichiarare confronto **INCONCLUDENTE**.

## Software subito, senza hardware

Simulare **7 nodi**, 2 isole, 1 ponte, 1 relay alternativo, 30 bundle sintetici con scadenza. Riprodurre tre tracce identiche e modificare soltanto la disponibilità del ponte. Iniettare contatti che non durano abbastanza per l'oggetto, code piene, duplicati, riavvii, consegne via più bearer e log mancanti. Confrontare ritardi, successo applicativo **simulato** entro deadline, carico per nodo, quota di bundle senza ricevuta, e numero di «isole con nessun recapito» nel modello. Non chiamare le simulazioni «PDR LoRa misurato».

**Accettazione:** nessun completamento senza receipt applicativa, nessun bundle duplicato accettato due volte, differenza BRIDGE_ON/OFF calcolata solo su workload e finestre confrontabili, unknown quando manca il denominatore, riserva/stop volontario rispettati. Il modello non deve dedurre che un ponte è indispensabile quando una traccia alternativa consegna correttamente.

## Campagna hardware e gate

**Prima fase:** 6–8 schede e 2 PC nello stesso laboratorio, creare contatti controllati fra gruppi (schermatura o distanza **solo se legale e sicura**, preferire finestre applicative programmate senza manipolare la radio), una scheda intermedia e bracci ON/OFF. Registrare invii effettivamente osservabili, RX dove disponibile, ricevuta app, code e tempi di ogni hop. **Seconda fase:** checkpoint scolastici autorizzati in due luoghi, con volontari e raccolta minimizzata di evidenze; ripetere più sessioni prima di descrivere resilienza geografica. Nessuna prova di campo dichiarata qui.

Non interrompere reti realmente utilizzate, allarmi o dispositivi di sicurezza. Prima di usare LoRa verificare adattatori, antenna, regole radio e consenso informato.

## Privacy, sicurezza, anti-duplicazione

Solo ID fittizi di prova, contatti aggregati per **campagna**, nessun GPS, tragitto, orario individuale o punteggio dei relay studenti; partecipazione revocabile senza pressione. Le ricevute sono firmate/autenticate dove disponibile e verificano l'identità dell'oggetto. Usare retention breve, accesso ai log per docenti.

UC-008 osserva grafi di contatto, UC-103 seleziona **dove aggiungere** un relay, UC-163 distribuisce copie fra failure domain, UC-233 simula il rientro dopo blackout e UC-275 confronta LoRa con il controllo senza LoRa. **UC-300 misura controfattualmente l'effetto della rimozione controllata di un singolo relay-ponte sulla consegna end-to-end, senza confondere opportunità o perdita di log con un guasto radio.**
