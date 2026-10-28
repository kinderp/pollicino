# UC-260 — DNA: cercare soltanto il fatto mancante per un'opportunità spiegabile

**Stato:** proposta documentale del 28 ottobre 2026; nessun codice sviluppato né risultato sperimentale. **Difficoltà:** alta (inferenza incrementale, policy, falsi positivi e comunicazioni opportunistiche).

## Problema e storia concreta

DNA riceve informazioni sparse fra laboratori disconnessi. A Rometta una classe cerca sensori per un esperimento. A Venetico una scuola dichiara di possedere una sonda. La regola di opportunità richiede però una calibrazione valida e l'autorizzazione al prestito. **Non sappiamo** queste due condizioni: non significa né che siano vere né che siano false. Replicare tutto il grafo attraverso LoRa sarebbe costoso e potrebbe esporre informazioni non pertinenti.

**User story:** come tutor di un progetto FSL voglio che il motore DNA mi spieghi quali premesse verificabili mancano per proporre una collaborazione, generi una **richiesta strettamente limitata** al detentore autorizzato di tali informazioni e riconcili la risposta ritardata prima di mostrare la deduzione.

## Attori e separazione dei livelli

Client richiedente, motore di inferenza DNA, detentore delle evidenze/sensore/laboratorio, autorizzatore o revisore, cache, relay studenti e un eventuale gateway. **DNA** gestisce fatti, necessità, regole e spiegazioni; **GeoTopic** può aiutare a individuare una stanza approvata; **PollicinoNet** trasporta riferimenti, domande autorizzate e prove con store-and-forward. I relay non diventano interpreti della verità dei fatti.

## Contratto di dati proposto

`goal_id`, `rule_id/version`, `known_premise_refs[]`, `missing_predicate`, `subject_scope`, `evidence_type`, `authorized_recipient`, `request_expiry`, `consent_scope`, `query_id`, `privacy_class`.

Stati distinti: **KNOWN_TRUE / KNOWN_FALSE / UNKNOWN / EVIDENCE_REQUESTED / EVIDENCE_RECEIVED_UNVERIFIED / EVIDENCE_VERIFIED / OPPORTUNITY_CANDIDATE / OPPORTUNITY_REVIEWED**. I bisogni estratti da domande (UC-251) sono segnali di interesse, **non** fatti. La mancata risposta non vale come risposta negativa. Nessun algoritmo può inferire un permesso di accesso dalla sola presenza di un sensore.

## Bearer

- **LoRa:** ID pseudonimi e digesti di richieste/risposte estremamente compatti se il payload e la policy lo consentono; mai grafo personale o contenuti privati in chiaro.
- **BLE:** scambio locale di richieste limitate e inventari minimi durante contatti.
- **Wi-Fi/Internet:** frammenti RDF, validazioni SHACL, manifest/provenienza e allegati.
- **USB/SD/trasporto fisico:** evidenze più grandi e documenti firmati fra scuole isolate.

## Esperimenti software immediati, senza schede

Implementare tre cache Python in partizioni distinte, 3 regole di opportunità e 20 fatti sintetici. Un mock del motore di inferenza è sufficiente per la prima fase; un LLM eventuale può **proporre** i predicati, non promuoverli direttamente in fatti verificati.

- Regola `requested_sensor AND available_sensor AND calibrated AND loan_authorized -> candidate`: inizialmente mancano le ultime due premesse. Emettere soltanto le due richieste realmente necessarie e autorizzate, senza pubblicare l'intero inventario.
- Iniettare risposte tardive, false, firmate da autorità sbagliata, scadute, contraddittorie e duplicate. Tenere separati claim ricevuti, evidenza verificata e approvazione umana.
- Ritirare la dichiarazione di disponibilità dopo la deduzione: il candidato diventa **REASSESS_REQUIRED** e non permane come opportunità approvata.
- Un nodo senza permessi per un'informazione sensibile non deve essere interrogato, né il fallimento dell'accesso deve svelare l'esistenza del fatto.
- Scegliere fra richiesta mirata e recupero generico confrontando **byte totali**, numero di query, completezza del risultato e attese simulate. Riportare anche i casi in cui la ricerca mirata è più lenta o peggiore.

**Criteri PASS:** zero proposizioni `UNKNOWN` promosse a `TRUE` senza evidenza conforme; nessuna query fuori scope; provata riconciliazione di ritardi, revoche e duplicati; spiegazione che indica le fonti esatte e le premesse ancora assenti. L'algoritmo non garantisce né verità semantica né disponibilità effettiva del bene.

## Campagna fisica e limiti

Prima tre processi su due PC, poi 4–6 schede con due checkpoint scolastici autorizzati fra Rometta e Venetico. LoRa per annunci realmente piccoli, Wi-Fi/USB per dichiarazioni e allegati. Misurare TX/RX, ritardo e byte di richieste, quantità di conoscenza verificabile recuperata e tasso di deduzioni corrette rispetto al dataset sintetico a ground truth. Solo dati fittizi nelle prove con minori; niente profili personali o geo-tracking.

## Privacy, sicurezza e non duplicazione

La minimizzazione è sostanziale: limitarne destinatario, classe informativa, finalità, conservazione e ripetizioni. Autenticare fonte e richiesta, anti-replay, rate limit, controllo di quota, eventuale revisore umano. Non inventare autorizzazioni alle operazioni reali.

**UC-024/034** trasportano interessi e query, **UC-147** riguarda lacune documentali Raiatea, **UC-244** spiega inferenze con fatti già disponibili, **UC-251** registra bisogni. **UC-260 collega un obiettivo inferenziale a premesse mancanti e produce acquisizione mirata, autorizzata, verificabile e differita**, con prova che `UNKNOWN` non diventi `TRUE`. Nessuna modifica radio.
