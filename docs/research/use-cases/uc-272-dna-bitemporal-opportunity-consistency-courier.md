# UC-272 — DNA: opportunità coerenti nel tempo dopo sincronizzazioni tardive

**Stato:** proposta documentale del **1 novembre 2026**; nessuna implementazione o prova eseguita. **Difficoltà:** alta (validità temporale, orologi incerti, provenienza e autorizzazioni). Il PHY LoRa congelato e i livelli radio non cambiano.

## Problema concreto

Tre laboratori disconnessi condividono un bisogno, un'offerta di sensori e un servizio di calibrazione. La richiesta a Rometta vale dalle 09:00 alle 11:00, l'offerta di Venetico dalle 14:00 alle 16:00 e il banco di Villafranca è disponibile nel pomeriggio. I frammenti DNA arrivano tutti insieme alle 17:00, trasportati da studenti relay. **Aver ricevuto tre fatti veri non significa che siano stati contemporaneamente veri**. Un motore ingenuo potrebbe proporre una collaborazione già impossibile.

**User story:** come tutor FSL voglio distinguere il tempo in cui un fatto era valido da quello in cui la rete lo ha ricevuto, per produrre opportunità temporalmente dimostrabili oppure ipotesi esplicitamente incerte, senza fingere che gli orologi dei nodi siano sincronizzati.

## Attori e PollicinoNet

Tre editori istituzionali autorizzati, due cache disconnesse, motore DNA e revisore, 4–8 schede LoRa fra checkpoint scolastici di Rometta, Venetico, Villafranca e Messina. Il motore **DNA** decide compatibilità logica/temporale; PollicinoNet conserva/inoltra **oggetti esatti, revisioni e annunci**, senza attribuire semantica agli orari. Un relay di studente non deve conoscere il contenuto dei fatti né essere tracciato.

## Contratto dati proposto

Ogni fatto contiene `fact_id/revision`, `issuer`, `statement`, `valid_from`, `valid_until`, `issued_at`, `observed_at` (se pertinente), `received_at` **locale e non autorevole**, `clock_basis`, `clock_uncertainty`, `signature`, `policy_scope`, `source_hash`. Non confondere:
- **tempo di validità:** intervallo in cui la dichiarazione è applicabile;
- **tempo di registrazione/arrivo:** quando una cache ne ha avuto notizia;
- **tempo di inferenza:** quando la regola ha elaborato le revisioni.

Un'offerta scaduta è un fatto storico, non una disponibilità presente. Un orologio impreciso produce `POSSIBLE_OVERLAP` o `UNKNOWN`, non un `CERTAIN_OVERLAP` inventato. Regole di normalizzazione fuso/UTC e intervalli semiaperti `[inizio,fine)` devono essere versionate; orari ambigui, fuso assente o `valid_until <= valid_from` vengono respinti. Il risultato include `rule_id/version`, `input_fact_ids/revisions`, `evaluated_at`, `candidate_interval`, `temporal_proof_status`, `expiry` e stato di revisione umana. Evidenze firmate sono **asserzioni di fonte**, non garanzie materiali che un bene sia davvero disponibile.

## Bearer e privacy

- **LoRa:** piccolo annuncio opaco di revisione/digest e scadenza grossolana **solo quando consentito**, non orari o inventari personali in chiaro.
- **BLE:** identificazione sicura delle versioni disponibili presso il checkpoint, se l'adapter lo consente.
- **Wi-Fi / Internet:** fatti RDF/JSON, regole, evidenze di clock e storici di revisione.
- **USB/SD/trasporto fisico:** scambio firmato dei frammenti completi dopo disconnessioni prolungate.

Controlli di accesso sulle premesse **prima** dell'inferenza e dell'esposizione del risultato. Non rispondere a query pubbliche confermando se un fatto riservato esista. Minori, identità personali, orari di presenza individuale e coordinate non entrano nelle fixture né nei beacon.

## Cosa possiamo provare ora, senza hardware

Tre cache/processi Python, dieci offerte/richieste fittizie, due regole e un trasporto simulato che ritarda, riordina, duplica e revoca i fatti. Test automatici:
1. tre fatti validi in intervalli **disgiunti** non generano un'opportunità attuale;
2. intervalli sovrapposti e orologi affidabili generano solo una **candidatura** spiegabile;
3. clock ±30 minuti su confini contigui dà `POSSIBLE_OVERLAP/UNKNOWN`, mai conferma certa;
4. `received_at` recente non prolunga `valid_until` e una notizia futura non equivale a fatto già valido;
5. late-arrival, doppia revisione, correzione o revoca ricalcolano lo stato mantenendo l'audit;
6. cache con informazioni diverse e identica vista autorizzata non devono divulgare l'esistenza di dati nascosti attraverso la spiegazione.

**Criterio PASS:** zero falsi `CERTAIN_OVERLAP` nel truth set e nessuna informazione protetta esposta; derivazioni riproducibili rispetto a snapshot, versioni e incertezza temporale. Misurare in simulazione stato di incongruenza, tempo fino alla correzione, byte e latenza logica. Nessun test è stato eseguito.

## Cosa richiede hardware reale

4–8 schede su due o tre checkpoint autorizzati; ciascuna scuola mantiene il proprio registro locale. LoRa porta riferimenti compatti, mentre oggetti e prove temporali viaggiano in BLE/Wi-Fi/USB. Introdurre ritardi reali di consegna **senza cambiare il timing radio congelato**; registrare TX/RX indipendenti, tempi locali e **incertezza** di clock, byte per bearer e instante di accettazione applicativa. Il test non richiede misurare la copertura della provincia. Non usare l'applicazione per prenotazioni o decisioni operative automatiche.

## Originalità rispetto al catalogo

- **UC-244** richiede fatti coerenti in una finestra, ma non definisce un **contratto verificabile di tempo valido vs tempo ricevuto e orologi incerti**; UC-272 mette proprio questa proprietà al centro dell'esperimento.
- **UC-260** cerca premesse mancanti; **UC-270** spiega risultati assenti; qui tre premesse possono essere tutte note e vere in momenti **non sovrapposti**.
- **UC-020/123** possono fornire evidenza temporale e stime di drift; **UC-153** tratta freschezza di sensori; UC-272 le riusa per l'inferenza DNA e non propone un nuovo sistema di sincronizzazione.

**Output atteso:** casi di conformità bitemporale e un protocollo di riconciliazione; non prestazioni o capacità già implementate.
