# UC-280 — Veicolo parcheggiato come data mule: la cabina lascia passare i contatti LoRa?

**Stato:** proposta documentale del **4 novembre 2026**; **nessun test eseguito, nessuna misura reale**. **Difficoltà:** medio-alta. PHY LoRa congelato, MAC, driver e firmware **non modificati**.

## Problema concreto / user story

Una scheda PollicinoNet trasportata in un'auto o in un mezzo autorizzato conserva messaggi per conto di due scuole. Non sappiamo però se, una volta all'interno dell'abitacolo chiuso, continui a scoprire i checkpoint: un messaggio non consegnato potrebbe essere imputabile alla schermatura, all'orientamento, al mancato incontro, alla seriale o a condizioni radio differenti. Non basta sapere che il veicolo è arrivato.

**Come responsabile del testbed** voglio confrontare, a veicolo **fermo** e in condizioni controllate, lo stesso relay fuori/dentro l'abitacolo e vicino/lontano dal finestrino, per decidere se lo scambio debba avvenire via LoRa, presso uno stop autorizzato tramite BLE/Wi-Fi, o con consegna fisica.

Questo **non** è un progetto di tracciamento dei mezzi e **non** propone prove su strada con minorenni.

## Attori, nodi e scenario della provincia di Messina

- Due checkpoint scolastici autorizzati (per esempio Rometta e Venetico; in seguito un terzo presso Villafranca/Messina), con PC collector.
- 4–6 schede LoRa già supportate: TX di riferimento, RX di riferimento indipendente se disponibile, relay nel veicolo e una scheda di riserva.
- Un veicolo **parcheggiato con autorizzazione del proprietario** in area sicura e non aperta al traffico, personale adulto e docente; studenti osservano/analizzano senza essere localizzati.
- Relay **store-and-forward**: riceve capsule sintetiche in una sessione, le porta al secondo checkpoint in una sessione successiva, rende disponibile una ricevuta applicativa. Non confondere avvicinamento del mezzo e consegna riuscita.

## Perché PollicinoNet, bearer e contratto

L'assenza di percorso continuo è normale: PollicinoNet può depositare capsule, conservare custodie e consegnare più tardi. **DISCOVERY** segnala disponibilità di un oggetto o contatto, **EXACT** conferma i byte verificati, **SEMANTIC** riguarda il contenuto e non la radio.

- **LoRa:** soltanto capsule di prova compatte e identificativi di campagna entro le capacità **esistenti** dell'adapter, con budget radio già documentato; non presumere che la scheda possa variare SF/potenza/antenna da software.
- **BLE:** scambio ravvicinato con il checkpoint, soltanto se hardware e adapter lo consentono.
- **Wi-Fi/Internet:** trasferimento di oggetti maggiori e dei log dopo lo stop, o come percorso di controllo sperimentale.
- **USB/SSD / trasporto fisico:** raccolta e trasporto dei log e dei file verificati (un mezzo può essere utile come data mule anche se la sua radio interna non è efficace).

Contratto **di prova applicativo** (non un nuovo frame radio): `{campaign_id, condition, checkpoint_id, tx_seq, tx_observed_status, rx_observed_status, accepted_object_id, evidence_source, clock_quality}`. `condition` vale ad esempio `OUTSIDE`, `CABIN_CLOSED`, `WINDOW_SIDE`; sono etichette di configurazione e non coordinate. Mai inventare `TX_ON_AIR` o contatori `RX_RADIO` che l'adapter non espone.

## Software subito (senza schede)

1. Generare tracce **sintetiche**, con seed, di due checkpoint, 4 relay e prove appaiate ABBA (esterno-interno-interno-esterno); introdurre contatti mancati, duplicati, RX ignoti e un ritardo nella consegna.
2. Parser e validatore dividono risultati in `TX richiesti`, `TX effettivamente osservabili`, `RX applicativi`, `EXACT accettati` e `UNKNOWN`. Il denominatore di una PDR radio va usato **solo** se è misurabile con sufficiente osservabilità; altrimenti riferire la mera percentuale end-to-end con definizione esplicita.
3. Verificare che uno spostamento *fittizio* del relay senza ricevuta `APP_ACCEPTED` non venga contato come consegna. Verificare che condizioni non confrontabili (antenna spostata, checkpoint cambiato, log persi) producano `INCONCLUSIVE`.
4. Confrontare tre politiche applicative a contatti identici: `LoRa-only microcapsule`, `LoRa DISCOVERY -> BLE/Wi-Fi bulk` e `stop fisico/USB`. Segnalare la migliore **solo nel dataset sintetico**, senza predire la provincia.
5. Salvare seed, schema e log di controllo. Accettazione proposta: nessuna PDR fisica fabbricata; nessuna falsa `APP_ACCEPTED`; politiche confrontate sulle stesse opportunità simulate.

## Prove hardware reali necessarie (non eseguite)

- Inventario radio, antenna, firmware e alimentazione; controllo dell'idoneità degli adapter senza modifiche. Verifica preventiva di frequenze, potenze, duty-cycle e autorizzazioni.
- Posizione dei checkpoint e distanza **costanti** nella prova appaiata; veicolo fermo, motore spento, antenna/configurazione costante, alternanza delle condizioni per ridurre l'effetto del tempo.
- Ripetere prove con sequenze note, ricevitori indipendenti quando disponibili, condizioni e log completi; distinguere mancata decodifica, mancata ricezione host e mancata accettazione applicativa secondo UC-277.
- Solo dopo il banco e il parcheggio, valutare un normale trasferimento **fra checkpoint** effettuato da un adulto autorizzato; nessuna prova radio durante la guida e nessuna registrazione degli spostamenti. Nessuna conclusione sui veicoli in movimento deriva dal test stazionario.

Metriche da misurare: RX validi e accettazioni per condizione, incertezza dei denominatori, differenza fra condizioni appaiate, tempo di consegna app, byte per bearer, energia se davvero strumentata. **Non** assumere copertura, effetto schermante, tempi o guadagno LoRa prima delle misure.

## Privacy, sicurezza e limiti

Niente targhe, video, GPS, percorsi, nomi studenti, messaggi privati o dati sull'uso del veicolo. Solo ID temporanei dei dispositivi/campagne; permesso del proprietario e della scuola; nessun incentivo a prove rischiose. Firma/integrità delle capsule, deduplica, budget di traffico, opt-out dei volontari e stop locale. Un miglioramento/peggioramento osservato non dimostra da solo che la causa sia la carrozzeria: posizione, orientamento, persone, ostacoli e condizioni RF sono confondenti.

## Differenza rispetto ai casi esistenti

- **UC-005 / UC-025:** veicoli e contatti programmati come data mule, non *idoneità reale del contatto radio dentro un abitacolo*.
- **UC-211 / UC-271:** montaggio dell'antenna e alimentazione; qui varia deliberatamente **l'ambiente veicolo** a parità di apparato.
- **UC-188 / UC-232 / UC-277:** fattibilità del payload, asimmetria e attribuzione perdite; qui il confronto appaiato è **fuori vs dentro un veicolo parcheggiato** e serve a scegliere il bearer al checkpoint.
- **UC-275:** valuta il valore marginale LoRa in generale; UC-280 valuta un **vincolo fisico specifico dei data mule veicolari**.

## Riferimenti metodologici (non prove della nostra rete)

- [LoRaWAN for Vehicular Networking: Field Tests for Vehicle-to-Roadside Communication, Sensors 2024](https://www.mdpi.com/1424-8220/24/6/1801): mostra che i collegamenti veicolari richiedono misure specifiche; il protocollo e i dispositivi dello studio non coincidono necessariamente con PollicinoNet.
- [Performance Measurements of LoRaWAN Connectivity for Links Through Metallic Shields, I2MTC 2024](https://research.unipd.it/handle/11577/3533921): motivazione per isolare schermature e condizioni. **Nessun numero dello studio è estrapolato al nostro testbed.**
