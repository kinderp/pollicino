# UC-317 — Peloritani: umidità delle lettiere vegetali con campioni e incertezza documentati

**Stato:** proposta didattica, non implementata. **Priorità:** media-alta (IoT/scienze). **Difficoltà:** medio-alta. **Dominio:** sensori ambientali, campioni fisici, laboratorio scolastico, store-and-forward.

## Problema risolto
Fra colline e costa, uno strumento economico può produrre letture su materiale vegetale morto, ma non è automaticamente una misura confrontabile della sua umidità. Materiale diverso, campione bagnato da pioggia, pesatura imprecisa, contenitore non identificato o procedura modificata rendono scorretto aggregare i numeri. Il caso introduce **una catena di osservazione a due livelli**: piccole capsule descrivono campione, metodo, incertezza e stato di revisione; i registri completi viaggiano in seguito. Nessuna lettura viene trasformata in indice di incendio o allerta.

## Scenario messinese (didattico, non operativo)
Tre classi o laboratori a Rometta, Venetico e Messina esaminano *materiali vegetali didattici reperiti lecitamente*, inizialmente campioni artificiali con masse fittizie e poi, solo previo protocollo e autorizzazione, lettiera secca in postazioni sicure. Le misure potrebbero essere raccolte in diverse giornate e consegnate da relay degli studenti a checkpoint scolastici. Nessuna pretesa che la rete LoRa colleghi direttamente i comuni; non è richiesto entrare in boschi, raccogliere materiale in aree protette o uscire con condizioni meteorologiche avverse.

## Attori e bearer
- Docente di scienze, gruppo osservatore, responsabile laboratorio, revisore della metodologia, 3 logger/cache, 3–4 nodi LoRa, eventuali data mule volontari.
- **LoRa:** microcapsule con ID campione pseudonimo, versione di protocollo, osservazione compatta, stato qualità, hash registro e richiesta di controllo.
- **BLE:** sincronizzazione locale dei logger compatibili.
- **Wi-Fi/Internet/USB o trasporto fisico:** fotografie autorizzate, dati grezzi, schede di pesata e campioni fisici (solo sotto gestione docente); no file grandi su LoRa.
- Se si decide una misura gravimetrica, la percentuale si calcola dalle masse nette con una procedura approvata: `100 * (mass_net_wet - mass_net_dry) / mass_net_dry`, soltanto con massa secca > 0 e unità compatibili. Non usare la formula per dedurre pericolo d'incendio.

## Dati minimi
`sample_id`, `site_coarse_public`, `collection_window`, `sample_kind`, `mass_method`, `balance_resolution`, `container_tare`, `wet_mass`, `dry_mass`, `unit`, `protocol_hash`, `sample_condition`, `method_validity`, `review_state`, `result_uncertainty`, `raw_log_hash`, `time_quality`.
Gli stati sono NOT_SAMPLED, COLLECTED, METHOD_INCOMPLETE, REVIEW_PENDING, VALID_FOR_EDUCATIONAL_COMPARISON, INVALID. Un campione mancato non vale 0%; una pesata non completata non vale "secco". Il tempo di osservazione non coincide con quello di consegna.

## Prova software immediata — progettata, NON eseguita
Simulare 3 siti, 36 campioni artificiali e 2 metodi ipotetici, includendo unità grammi/chilogrammi, tara dimenticata, massa secca nulla, massa umida inferiore alla secca, campioni misti, protocollo cambiato, dati mancanti, duplicati e versioni di revisione arrivate fuori ordine. Generare output in CSV/JSON, verificare gli invarianti con test deterministici e distinguere i risultati sintetici da quelli di campo.

**Criteri di accettazione:**
1. Nessun calcolo se la massa netta secca è nulla/non positiva o le unità e la tara sono sconosciute.
2. Dati INVALID, METHOD_INCOMPLETE o NOT_SAMPLED non vengono aggregati come validi e non diventano misure zero.
3. Metodi o tipi di lettiera incompatibili non vengono confrontati come lo stesso protocollo senza revisione.
4. Le correzioni tardive non spariscono a causa di record arrivati dopo, e gli hash identificano la versione dei registri.
5. Nessun output produce previsione, classificazione del rischio incendi o indicazione d'intervento per protezione civile.
6. Un messaggio LoRa consegnato è distinto dal dataset integrale verificato su bearer ricco.

## Hardware e verifiche reali — non eseguite
Prima **4 schede LoRa**, 2 PC, una bilancia scolastica idonea e campioni dimostrativi in aula; logging di trasmissione, ricezione e ricevuta applicativa. Eventuali metodi di essiccazione/pesatura reali richiedono strumentazione idonea e *supervisione professionale*, non improvvisazione con stufe domestiche o dispositivi caldi. In fase avanzata usare soltanto aree autorizzate e protocolli scientifici validati. Registrare effettiva risoluzione/incertezza della bilancia e condizioni del campione. Nessuna stima di copertura radio, PDR o sensibilità del sensore è possibile prima delle prove.

## Privacy e sicurezza
Evitare tracciati GPS degli studenti, nomi di proprietari e fotografie di persone; posizioni pubbliche a granularità sufficiente per il disegno sperimentale; niente raccolta di fauna/flora protetta o attività che aumentino rischio incendi; nessuna diagnosi ambientale operativa.

## Anti-duplicazione
- **UC-197:** microclima per condizioni meteorologiche associate a possibili incendi; qui **campione fisico di lettiera + masse nette, protocollo, controllo qualità e revisione**.
- **UC-269:** conducibilità elettrica del suolo negli orti, variabile/materiale/prova diversi.
- **UC-031/166:** calibrazioni e cross-calibration generiche; qui la validità del **metodo gravimetrico su campioni specifici**.
- **UC-204:** collega campione fisico e misure digitali; qui introduce comparabilità delle **masse umida/secca**, impedisce aggregazioni false e non presume equivalenza fra campioni.
- **UC-302/309:** gestione contatori pioggia e sensori PM; qui controllo dei dati di campionamento vegetale con massa, tara e protocollo.

## Fonti metodologiche
- National Wildfire Coordinating Group, `Fuel Moisture Sampling` (riferimento scientifico, non procedura operativa scolastica): https://www-nwcg.fs2c.usda.gov/publications/pms437/fuel-moisture/fuel-moisture-sampling
- USDA Forest Service (2016), valutazione dei metodi di campionamento dell'umidità dei combustibili: https://research.fs.usda.gov/treesearch/52252

**Confini:** nessuna raccolta o misura fisica, niente attività o indicazioni antincendio operative, niente modifica a PHY LoRa congelato, MAC, driver o firmware.
