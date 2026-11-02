# UC-274 — Collisioni degli indizi DISCOVERY e risoluzione EXACT

**Stato:** proposta documentale del 2 novembre 2026; nessuna funzionalità implementata né test eseguito. **Difficoltà:** medio-alta (identità, riservatezza, protocollo di fallback). Nessuna modifica al PHY LoRa congelato, MAC, driver o firmware.

## Problema concreto e user story

Un laboratorio di Rometta annuncia un documento Raiatea, uno di Venetico un dataset, uno di Villafranca una versione di un modello AI. Per risparmiare byte LoRa, PollicinoNet può pubblicare **indizi brevi di disponibilità** (non l'identità integrale degli oggetti). Due oggetti diversi possono produrre lo stesso indizio: un destinatario potrebbe scaricare il contenuto sbagliato o considerare verificato un file solo perché il riferimento breve coincide.

**Come studente che cerca un artefatto**, voglio scoprire candidati con pochissimi byte, ma **non voglio che un indizio ambiguo diventi una prova d'identità**; voglio un esito esplicito `UNIQUE_CANDIDATE`, `AMBIGUOUS`, `UNKNOWN` o `UNAUTHORIZED`.

## Attori e perché PollicinoNet

Editori autorizzati, cache di scuola, 4–8 relay volontari fra checkpoint a Rometta, Venetico, Villafranca e Messina, client richiedente e verificatore finale. Il relay conserva/inoltra byte opachi, senza dover distinguere il documento dal modello. Il caso sfrutta i contratti distinti **DISCOVERY** (indizio economico), **EXACT** (identità integrale, policy e verifica finale) e **SEMANTIC** (eventuale ricerca per descrizione: mai prova di identità). Non assumere una particolare dimensione di payload o capacità dell'adapter radio: prima verificare ciò che è già supportato.

## Contratto applicativo proposto (non formato radio)

`announcement = {experiment_id, hint_scheme_version, namespace_class, hint_bits, hint_value, expiry, issuer_scope, nonce, signature_or_auth_ref}`. Il `hint_value` può essere un prefisso/derivato pubblico versionato del riferimento; **non è un hash completo, una firma o un segreto**.

La cache autorizzata risolve `(scheme, namespace, hint)` in un insieme limitato di **candidati**. Il client può richiedere un manifest EXACT con `content_sha256` completo, versione, lunghezza, issuer, uso consentito e firma; il contenuto ricostruito è accettato solo dopo verifica integrale dell'hash, firma/policy quando applicabili e associazione alla richiesta originale. Una collisione è un normale caso di protocollo; un numero eccessivo di candidati causa `BOUNDED_AMBIGUITY`, non trasferimenti illimitati né scelta del primo elemento. Un annuncio scaduto o non autorizzato non viene promosso a oggetto valido.

Non fissare `hint_bits` in questa scheda: confrontare varie lunghezze e i costi; la quantità di collisioni dipende anche dal numero e dalla distribuzione degli oggetti. Eseguire controlli negativi con collisioni costruite intenzionalmente, oltre ai dataset casuali, senza usare questi test come prova di resistenza crittografica.

## Bearer e flusso

- **LoRa:** solo hint breve e contesto minimo consentito, compatibili con adapter e budget di trasmissione effettivi.
- **BLE:** richiesta autorizzata dei candidati / manifest quando due nodi si incontrano.
- **Wi-Fi/LAN/Internet:** manifest completo, contenuto, eventuale checkpoint di modello o verifiche più costose.
- **USB/SD/trasporto fisico:** oggetti e manifest portati in differita fra PC scolastici non connessi.
- Nessun obbligo di ripetere in LoRa un manifest lungo o di introdurre frammentazione PHY.

## Cosa testare subito in software

Tre cache virtuali, 1.000–10.000 oggetti fittizi e un trasporto a eventi con perdita, ritardo, replay, duplicati e disconnessioni. Fixture deterministiche con indizi di 8/12/16/24 bit (valori **esclusivamente sperimentali**, non parametri da distribuire su LoRa). Test:

1. due oggetti con lo stesso hint => `AMBIGUOUS`, mai accettazione silenziosa del primo;
2. una singola candidatura ma bytes finali/hash diversi => `REJECT`;
3. hint valido ma manifest firmato non disponibile, scaduto o senza permesso => `UNKNOWN/UNAUTHORIZED`, non `ACCEPT`;
4. replay e oggetti cancellati non riabilitano disponibilità;
5. molte collisioni intenzionali => budget di query/risposta e memoria rispettato, con fallback dichiarato;
6. nessuna informazione su contenuti riservati è inferibile tramite risposte differenziate a richieste non autorizzate; verificare anche il **rischio di correlazione degli annunci ripetuti**.

**PASS software:** zero false accettazioni EXACT e zero promozioni non autorizzate sulle fixture; collisioni riconosciute e consumo entro i limiti dichiarati. Report: tasso di ambiguità, query addizionali, byte per bearer, oggetti EXACT verificati e timeout. Nessun PASS dichiarato prima di eseguire i test.

## Prove fisiche necessarie

Due checkpoint fissi autorizzati, 4–8 schede già supportate dal progetto e due PC; preparare **in anticipo** due artefatti con hint uguale e hash integrale differente. Annunciare soltanto gli hint di prova su LoRa; far viaggiare le richieste e i manifest via BLE/Wi-Fi o trasporto fisico e verificare il risultato sul PC destinatario. Registrare TX effettive, RX indipendenti, ritardi di riconciliazione, byte/airtime e conferma applicativa. I nodi degli studenti possono successivamente fare store-and-forward, **senza log degli itinerari**. Rispettare frequenze, potenze e limiti di occupazione applicabili.

## Privacy e differenza dai casi già presenti

Indizi ripetuti potrebbero permettere correlazioni; minimizzare durata, visibilità, retention e contesto. Non usare nomi di studenti, documenti privati o coordinate. L'hash di un oggetto pubblico **non prova l'autorizzazione** a rivelarlo.

**UC-024** porta richieste a cache sconosciute, **UC-152** riconcilia inventari, **UC-230** confronta envelope fra bearer, **UC-262** ricompone piccoli frammenti LoRa. **UC-274** isola un altro rischio: **identificatori di discovery volutamente compressi e ambigui, che non devono mai essere elevati a identità EXACT**. Risultato atteso: un resolver con test di collisione e budget misurabili, non prestazioni radio presunte.
