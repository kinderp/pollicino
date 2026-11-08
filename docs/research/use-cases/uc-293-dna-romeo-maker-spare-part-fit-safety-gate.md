# UC-293 — DNA/Romeo: trovare ricambi compatibili senza promettere montaggi non verificati

**Stato:** proposta documentale del **8 novembre 2026**; nessuna implementazione, test o prova di montaggio eseguiti. **Difficoltà: medio-alta/alta** (semantica delle specifiche, sicurezza elettrica/meccanica e conflitti offline). PHY LoRa congelato e altri livelli radio invariati.

## Problema e scenario messinese

Nel laboratorio di Rometta il robot didattico **Romeo** richiede una staffa per il pan-tilt o un componente di ricambio. Un laboratorio di Venetico dispone di un pezzo apparentemente adatto; una terza scuola a Villafranca possiede una stampante 3D. Una descrizione generica «servo compatibile» non dimostra che **tensione, assorbimento, segnali, connettori, dimensioni, carichi e fissaggi** siano adatti. Una sostituzione errata può danneggiare hardware o provocare movimenti indesiderati.

**User story:** come responsabile del robot, voglio ricevere da DNA **possibili componenti o servizi**, con una checklist di compatibilità e provenienza; ciò che non è stato verificato deve restare `UNKNOWN` e **nessun montaggio, comando o alimentazione può essere autorizzato automaticamente**.

## Attori, nodi e valore di PollicinoNet

Richiedente Romeo, docente che valida le specifiche, laboratori che offrono componenti/parti, motore DNA, eventuale DNATrace per provenance non personale, Raiatea per recuperare *datasheet* con hash/versione, 4–8 relay volontari, macchina di fabbricazione supervisionata. L'offerta e la richiesta possono emergere a ore diverse: il **rendezvous store-and-forward** accoppia bisogno e disponibilità senza un catalogo sempre online. Il trasferimento fisico rimane un passaggio distinto dalla compatibilità e dall'accettazione finale.

- **DISCOVERY:** `need:pan_tilt_bracket`, `offer:servo_mount` o `capability:3d_print` con identificatori temporanei e scadenza.
- **EXACT:** BOM/versione Romeo, scheda tecnica, unità, tolleranze e provenienza, hash del file CAD, autorizzazione, stato dell'ispezione fisica e della consegna.
- **SEMANTIC:** il motore DNA suggerisce candidati e relazioni; **non inventa specifiche o certificazioni** se non disponibili.

## Bearer

- **LoRa:** riferimenti corti autorizzati a bisogni/offerte, disponibilità approssimata, stato `REQUIRES_REVIEW` o `REJECTED`, quando le capsule sono compatibili con l'adapter attuale.
- **BLE:** incontro locale per check di etichetta e metadati brevi.
- **Wi-Fi/LAN/Internet:** BOM, disegni CAD, datasheet completi, fotografie, controlli dimensionali e ricevute; accesso Internet opzionale per fonte ufficiale del datasheet.
- **USB/SSD e trasporto fisico:** CAD o parti consentite fra sedi; il pezzo viene consegnato **solo** con consenso e verifica supervisionata.

## Contratto dati proposto

`PartNeed = {need_id, robot_bom_version, component_role, supply_voltage_range?, signal_level?, connector?, mechanical_envelope?, weight_limit?, torque_limit?, intended_use, expiry, authorization}`.

`PartOffer = {offer_id, part_model_exact, documentation_hash?, publisher, observed_dimensions?, declared_specs?, provenance: MANUFACTURER|MEASURED|UNVERIFIED, availability_epoch, constraints, expiry}`.

`FitAssessment = {need_id, offer_id, field_checks: [{field, expected, offered, unit, result: MATCH|MISMATCH|UNKNOWN}], verdict: INCOMPATIBLE|UNKNOWN|CANDIDATE_FOR_REVIEW|HUMAN_APPROVED, reviewer_role?, evidence_hashes[], decision_epoch}`.

Le unità devono essere esplicite; `UNKNOWN` non vale `MATCH`. Una misura con tolleranza non supporta automaticamente una garanzia di accoppiamento fisico. Le informazioni dei datasheet sono **dati di input da verificare**, non affermazioni del sistema.

## Test software immediati, senza robot

1. Fixture con **20 parti completamente inventate**, tre BOM robot e due stampanti virtuali; alcuni componenti differiscono solo per tensione, pinout, filetto o passo dei fori.
2. Motore deterministico che restituisce `INCOMPATIBLE` quando una condizione necessaria è contraddetta, `UNKNOWN` quando manca una condizione, `CANDIDATE_FOR_REVIEW` per tutte le condizioni note compatibili.
3. Simulare tre cache disconnesse con offerte duplicate, aggiornamenti tardivi, revoche di disponibilità e due proposte concorrenti sullo stesso pezzo.
4. Associare ogni suggerimento alla fonte e alla versione delle specifiche; bloccare la promozione a `HUMAN_APPROVED` senza evento firmato del docente.
5. Integrare in sola simulazione UC-047 (servizio di stampa) e UC-042 (passaggio fisico); verificare che il «pezzo consegnato» non equivalga a «pezzo montato e sicuro».

**Accettazione:** nessun dato mancante trasformato in compatibilità; incompatibilità elettriche/meccaniche respinte; vecchie offerte non risorgono dopo revoca; report di inferenza spiegabile; nessun comando robotico generato; test `PASS/FAIL/UNKNOWN/NOT_TESTED` marcati `SIMULATED`. Non eseguiti.

## Hardware richiesto dopo il gate software

Due PC separati, 4–6 schede LoRa per micro-annunci, robot **disalimentato**, staffe dimostrative non pericolose e personale autorizzato. Confrontare prima una checklist su un **modello o mockup inerte**, poi eventuali dimensioni meccaniche reali sotto supervisione; prova elettrica o attuazione solo con procedura distinta, alimentatori idonei e personale competente. **Non collegare mai componenti sconosciuti per vedere se funzionano.** Nessun controllo remoto attuativo attraverso il relay.

Un primo dimostratore può usare **solo staffe stampate** e confrontare disegni/tolleranze: è adatto a un percorso FSL senza esposizione ai rischi di servo alimentati.

## Privacy, autorizzazioni e confini anti-duplicazione

Nessun nome/indirizzo di studenti o percorso dei relay; pubblicare solo gli inventari approvati, mantenere riservate le schede tecniche/licenze non ridistribuibili, firme di docenti/revisori, consegne supervisionate. I nodi non possono aggiornare l'inventario altrui come fonte autorevole.

**UC-015** tiene l'inventario, **UC-047** trasporta lavori di fabbricazione, **UC-043** cerca beni e **UC-261** approva missioni AI per Romeo. **UC-293 introduce il gate esplicito di compatibilità fisica/elettrica e provenance delle specifiche** *prima* che un suggerimento DNA diventi una sostituzione autorizzata. Non è un sistema di certificazione di sicurezza.
