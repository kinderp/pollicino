# UC-251 — Grafo DNA dei bisogni estratti da domande, senza inventare fatti

**Stato:** proposta documentale del 25 ottobre 2026; non implementata, nessun test eseguito. **Difficoltà:** medio-alta (modellazione epistemica, privacy, valutazione NLP).

## Problema e scenario
Tre laboratori offline formulano domande del tipo «Dove trovo un sensore di umidità?», «Qualcuno sa calibrare un sensore?» e «Si può condividere un kit di misurazione?». Se registriamo le domande come affermazioni, il sistema potrebbe erroneamente dedurre che il kit *esiste* o che qualcuno *sia disponibile*. Se le ignoriamo, perdiamo però segnali preziosi di bisogno e opportunità di collaborazione.

**User story:** «Come docente, voglio vedere che più gruppi chiedono strumenti analoghi, senza far passare le domande degli studenti per fatti e senza pubblicare i testi personali».

## Attori e nodi
Client locali di domanda, estrattore deterministico o LLM opzionale con validazione, motore DNA, aggregatore scolastico, reviewer, cache e relay volontari. Esempio: richieste sintetiche da Venetico e Rometta raggiungono un aggregatore a Villafranca quando si incontrano i relay.

## Modello minimo
Tipo `InformationNeed`, distinto da `Fact`, `Offer` e `DerivedOpportunity`: `need_id`, topic/schema versionati, entità/attributi richiesti, modalità interrogativa, ambito pubblico approvato o privato, origine pseudonima *solo locale*, scadenza, access policy e provenienza della classificazione. Conservare il testo originale sul dispositivo o in archivio autorizzato; la rete trasporta soltanto una richiesta strutturata approvata o un aggregato sufficientemente ampio.

Un parser estrae ad esempio `need(category="sensore_ambientale", capability="calibrazione")`; **non produce** `exists(sensor)`, `available(calibration)` o `located_at(student, place)`. L'LLM può suggerire tag o entità, ma il validatore assegna `REVIEW` quando il contesto è insufficiente o rischioso. Rispettare la distinzione `QUESTION` / `ASSERTION` / `UNKNOWN`. Un'eventuale offerta o risposta arriva più tardi come evento autonomo firmato, con revisione umana.

## Perché PollicinoNet e bearer
Le domande categorizzate sono micro-fatti relativi a **domanda di conoscenza**, non risposte. LoRa è possibile solo per identificatori/riepiloghi pubblicabili e molto compatti; BLE scambia piccoli batch autorizzati; Wi-Fi/Internet porta descrizioni e risposte documentate; USB/trasporto fisico porta archivi per il revisore. I relay store-and-forward raccolgono contributi anche se i laboratori non sono connessi simultaneamente.

## Esperimento software immediato
Corpus sintetico di 120 frasi: 60 domande, 30 affermazioni, 15 richieste implicite, 15 casi ambigui; metà contiene nomi fittizi e luoghi privati che devono essere rimossi, non diffusi. Annotare un gold standard docente e confrontare: baseline a regole semplici, classificatore locale, eventuale LLM con output vincolato. Introdurre duplicati, versioni dello schema diverse, scadenze, annullamento della domanda e la falsa risposta «il kit è a scuola».

Criteri: **zero fatti assertivi costruiti soltanto da domande**; provenienza per ogni bisogno registrato; topic sconosciuto => `REVIEW/UNKNOWN`; i messaggi LoRa non contengono testo personale; bisogni ritirati non vengono ripresentati come attivi quando riemerge una replica obsoleta. Misurare precisione/recall dei bisogni rispetto al gold, falsi claim, byte trasferiti, ritardi, quota di richieste ambigue e falsi match; non attribuire benefici a dati reali inesistenti.

## Hardware necessario
4–8 schede, due PC isolati, una cache e due checkpoint scolastici autorizzati. Trasportare **solo richieste sintetiche/aggregate** e successivi riferimenti a risposte verificate, misurando TX/RX, tempi reali, byte e allineamento semantico finale. Eventuali domande personali reali richiederebbero autorizzazioni e un'analisi dei rischi separata; non usarle nel primo campo.

## Privacy e sicurezza
Minimizzare, aggregare con soglia per evitare unicità, consenso e stop locale, accessi e retention limitati, niente inferenze su minori o bisogni sanitari, nessuna trasformazione automatica di richiesta in contatto personale. Provenienza/attributi di autorizzazione devono accompagnare ogni risultato. Lo pseudonimo da solo non rende anonima una domanda rara.

## Distinzione dai casi esistenti
UC-024 cerca un **oggetto già definito**; UC-083 spedisce sottoscrizioni future; UC-100 riassume la domanda per decidere il caching; UC-244 deriva opportunità da **fatti/offerte autorizzati**. **UC-251 costruisce invece un grafo tipizzato di bisogni *dalle sole domande*, senza creare falsi fatti**, che sarà riutilizzabile in seguito da un motore di ricerca o inferenza proattiva. Nessuna modifica al PHY LoRa.
