# UC-276 — DNA: privacy delle inferenze a mosaico da frammenti apparentemente innocui

**Stato:** proposta documentale del 2 novembre 2026; non implementata né verificata. **Difficoltà:** alta (politiche sulle derivazioni, riconciliazione offline e rischi di inferenza). PHY LoRa congelato e infrastruttura radio invariati.

## Problema concreto

Tre bacheche GeoTopic pubblicano dati **singolarmente autorizzati**, per esempio che un laboratorio prepara un evento, che una risorsa è prenotata in una determinata fascia e che esiste una richiesta legata a un piccolo gruppo fittizio. Il motore DNA può unirli e dedurre un'informazione sulla **disponibilità, sull'appartenenza o sugli interessi** di un individuo o di un gruppo ristrettissimo. Nessuna premessa era privata isolatamente, ma il **risultato derivato** può essere inopportuno da pubblicare.

**User story:** come gestore di DNA/GeoTopic voglio che la valutazione della privacy avvenga **prima dell'uscita dell'inferenza**, non solo controllando i permessi delle premesse. Un'inferenza utile al docente internamente potrebbe non essere adatta a un annuncio pubblico LoRa.

## Attori e valore di PollicinoNet

Editori della scuola, motore DNA, revisore autorizzato, client GeoTopic, due cache/RDF store intermittenti, relay studenti opachi e un collector. PollicinoNet distribuisce **frammenti consentiti** e revisioni tramite store-and-forward; il motore DNA produce una derivazione con provenance, ma la cache che la diffonde verifica un **vincolo sul risultato**. La rete non decide chi possa conoscere una relazione derivata; questa è una scelta applicativa e di governance.

## Contratto proposto

`Fact = {id, issuer, revision, category, allowed_purposes, audience, expiry, source_hash, signature}`.
`Derivation = {rule_id/version, input_ids/revisions, candidate_claim, provenance, temporal_state, derived_sensitivity, audience_candidate, policy_version, review_state, expiry}`.
`DisclosureDecision = {result: ALLOW_LOCAL | ALLOW_AGGREGATE | REQUIRE_REVIEW | DENY_PUBLIC | UNKNOWN, reason_code, evaluated_at, approved_audience, policy_version}`.

**Regole non negoziabili:**
- I permessi degli input sono necessari ma **non sufficienti**. Ricontrollare la nuova informazione (effetto mosaico).
- Separare `inference_generated`, `inference_validated` e `inference_publishable`. `VALID` non significa `PUBLIC`.
- In condizioni offline con policy o consenso mancanti, rifiutare la pubblicazione esterna e mantenere l'analisi solo dove già autorizzata; non assumere implicitamente consenso.
- Aggregazione/coarsening, soglie di numerosità e pseudonimi sono **mitigazioni da valutare**: nessuna garantisce automaticamente anonimato.
- Revoche, variazioni di contesto e nuove inferenze devono invalidare/ricontrollare decisioni precedenti; una replica non autorizzata **non può promettere cancellazione immediata** su nodi non raggiungibili.
- Le spiegazioni non devono rivelare l'esistenza di fatti nascosti a utenti non autorizzati; un output `DENY_PUBLIC` non deve includere il contenuto negato.

## Bearer

- **LoRa:** solo annuncio **esplicitamente autorizzato** di opportunità aggregate e non sensibili; altrimenti **nessun broadcast**, neppure digest stabile se consente correlazioni.
- **BLE:** sincronizzazione selettiva fra cache verificate; richieste autorizzate di policy/revisioni.
- **Wi-Fi/Internet:** grafi RDF, regole, audit riservati e revisione umana, con autenticazione.
- **USB/SD/trasporto fisico:** esportazione cifrata/firmata per revisore, con scopo e scadenza dichiarati.

## Esperimento immediato in software

Tre processi Python isolati, 80 fatti e 20 inferenze **interamente sintetici**, usando luoghi e persone inventati. Costruire due viste identiche per il pubblico ma con attributi nascosti differenti; riprodurre anche combinazioni di dati singolarmente pubblici che producono un attributo derivato protetto. Criteri PASS/FAIL:
1. inferenza logicamente valida ma sensibile => `DENY_PUBLIC` oppure `REQUIRE_REVIEW`, mai auto-annuncio;
2. lo stesso output per due mondi che differiscono soltanto nei fatti non autorizzati al richiedente (controllo empirico di **noninterferenza**, non dimostrazione formale);
3. riunificazione tardiva di cache e nuova policy => decisione ricalcolata prima di una nuova pubblicazione;
4. un fatto scaduto o revocato non continua ad autorizzare una derivazione;
5. tentativi di enumerazione, richieste ripetute e hint correlabili non rivelano dimensione, identità o interessi dei gruppi fittizi;
6. se la base documentale è insufficiente, `UNKNOWN` e nessuna pretesa di confidenza artificiale.

**Esito atteso:** matrice decisionale e report di divulgazioni indebite (target zero nelle fixture), falsi blocchi e costo di revisione. Per dimostrare proprietà più forti occorrerebbero analisi formali e audit privacy indipendenti. Nessun test eseguito.

## Prove fisiche / scenario Messina

Prima un esperimento software tra due checkpoint scolastici; poi 4–6 schede di prova fra Rometta, Venetico e Villafranca per trasferire esclusivamente **riferimenti di test già approvati**. Simulare un relay studente che riceve una revisione dopo molte ore: la cache destinataria deve applicare la policy nuova **prima** di rendere pubblico il risultato. Misurare consegne di policy e revoche, byte e tempo di convergenza fra cache, senza raccogliere identità, mobilità, orari o interessi di studenti. Per i controlli di policy non serve misurare RSSI/copertura; se si usa la radio, raccogliere logs TX/RX senza confondere consegna con autorizzazione.

## Novità rispetto al catalogo

**UC-244** riguarda inferenza spiegabile; **UC-248** filtra annunci in locale senza profili centralizzati; **UC-270** oscura premesse nelle spiegazioni `why-not`; **UC-189** analizza linkability di metadati di rete; **UC-077/139** affrontano propagazione/audit delle cancellazioni. **UC-276 aggiunge il gate di divulgazione dell'output *derivato da più frammenti***: proteggere solo i singoli input non basta. Non sostituisce una DPIA, una revisione GDPR o il consenso degli interessati.
