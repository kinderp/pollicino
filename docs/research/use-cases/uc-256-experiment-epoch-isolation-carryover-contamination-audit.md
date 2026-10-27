# UC-256 — Isolamento degli esperimenti e contaminazione delle code fra campagne

**Stato:** proposta documentale del 27 ottobre 2026. Non implementata; nessuna misura radio effettuata. **Difficoltà:** medio-alta.

## Problema risolto e storia concreta

Una rete di schede LoRa negli zaini degli studenti è utilizzata il lunedì per la campagna A (confronto di due strategie di routing) e il martedì per la campagna B (invio di osservazioni IoT). Alcuni relay erano spenti lunedì e riappaiono martedì con messaggi della campagna A ancora in coda. Se una ricevuta tardiva viene conteggiata nella B, o una vecchia configurazione modifica i nodi durante B, il risultato sembra migliore o peggiore senza motivo.

**User story:** come docente responsabile del testbed voglio avviare B senza cancellare arbitrariamente gli oggetti legittimi rimasti in custodia da A, ma senza permettere a pacchetti, metriche o comandi della A di contaminare i risultati della B.

Il problema non è che le campagne siano sovrapposte nel calendario: è il **trascinamento causale dello stato applicativo** attraverso partizioni, spegnimenti e incontri successivi.

## Attori e nodi

- Coordinatore e revisore delle campagne presso la scuola.
- 6–10 schede studente volontarie come relay store-and-forward; due checkpoint scolastici autorizzati (prima nello stesso laboratorio, poi per esempio Rometta e Venetico).
- Nodo di osservazione indipendente, collector e due applicazioni di test con destinatari separati.
- Nessun docente deve ricostruire itinerari personali: contano solo identificativi temporanei di tentativo, campagna e messaggio.

## Perché PollicinoNet è adatto

Nelle reti intermittenti l'ordine di arrivo non coincide con l'ordine di creazione. Una chiusura di campagna non raggiunge immediatamente ogni nodo; vecchi oggetti possono essere **ancora validi per la consegna reale**, ma **non validi per il denominatore della nuova prova**.

Contratto applicativo proposto (non requisito del PHY):

    campaign_id, run_id, isolation_epoch, manifest_hash,
    message_id, message_origin_run, policy_hash, intended_recipient,
    accepted_at_checkpoint, evidence_ref, state

Il nodo classifica ogni oggetto come ACTIVE_IN_RUN, LATE_FROM_OLD_RUN, QUARANTINED_UNKNOWN_RUN, NOT_ELIGIBLE o EXPIRED. Le etichette sono **giudizi del testbed**, non risultati del driver radio. Per contenuti di produzione non sperimentali sono previsti namespace e code logicamente separati: la fine di una campagna **non implica** la cancellazione indiscriminata.

- **DISCOVERY:** digesti brevi del manifest/epoch ammessi.
- **EXACT:** identificativi, hash, ricevute firmate e log di audit.
- **SEMANTIC:** esclusione motivata dal conteggio, con ragioni verificabili.

## Bearer disponibili

- **LoRa:** soltanto annunci di campagna, ID/epoch e messaggi di prova compatti *se* i limiti effettivi di payload e airtime lo consentono.
- **BLE:** scambio di riepiloghi e reconciliations durante incontri controllati.
- **Wi-Fi/LAN e Internet:** trasporto di log, manifest completi e analisi, senza richiedere Internet per il funzionamento.
- **Supporto fisico/USB/SD:** grandi evidenze e code da analizzare, in forma autorizzata e verificata tramite hash.

## Test immediati interamente software

Simulare otto relay, due checkpoint e due run A/B con trasporto che ritarda, riordina e duplica messaggi. Almeno i seguenti casi di test devono essere automatici:

1. Oggetto A arriva durante B: viene consegnato secondo il suo contratto originale, ma **mai contato come successo B**.
2. Una vecchia istruzione di esperimento arriva dopo il passaggio a un nuovo epoch: non cambia la configurazione corrente.
3. Un relay si riavvia fra A e B senza perdere la custodia già confermata (collegamento a UC-253).
4. Due campagne condividono un destinatario e un content hash: non si deduce che un ID di messaggio appartenga all'altra.
5. Una ricevuta A arriva dopo la chiusura di B: resta attribuita ad A; l'ordine dei log non altera il risultato.
6. Stato di campagna sconosciuto o firme mancanti: niente conteggio positivo, ma categoria UNKNOWN esplicita.
7. Prove B contro dataset pulito e dataset con ritardi incrociati: il numero di successi validi per B deve essere identico.

Misure software: percentuale di attribuzioni erronee (obiettivo zero nei casi deterministici), copie in quarantena, memoria occupata per run, costo degli ID/metadata, tempo di riconciliazione. Non chiamare queste metriche PDR o misure radio.

## Prove fisiche e scenario Messina

**Fase 1:** 4 schede in laboratorio, checkpoint A/B, sequenza di riavvii e un nodo volutamente tenuto offline. **Fase 2:** 6–10 nodi fra checkpoint scolastici autorizzati nell'area Rometta–Venetico–Villafranca, con relay trasportati volontariamente lungo normali spostamenti e senza tracciare individui.

Eseguire due campagne successive e ripetere il test invertendone l'ordine. Conservare log TX/RX dove realmente osservabili, firmware/config hash, prove delle consegne e ricevute **applicative**. Occorre verificare fisicamente se esistono vecchi messaggi consegnati nella seconda finestra e se il collector li classifica correttamente. Le statistiche della campagna non sostituiscono misure indipendenti di radio, contatto, energia o airtime.

## Privacy e sicurezza

Manifest e chiusure firmati; blocco anti-replay su epoch; niente ID studenti, GPS, indirizzi, orari personali o classifiche dei portatori. Identificativi temporanei e conservazione breve di log. Stop volontario locale da UC-217. Separazione fra code sperimentali e messaggi non sperimentali; la quarantena non autorizza la lettura di contenuti cifrati. Gli epoch incerti restano incerti finché manca un'autorità verificabile.

## Originalità e collegamenti

**UC-097** distribuisce manifest e raccoglie evidenze; **UC-178** valuta i denominatori mancanti; **UC-183** confronta politiche equamente; **UC-226** coordina campagne contemporanee; **UC-240** limita i loop. **UC-256 aggiunge un isolamento verificabile fra run successivi, con arretrati tardivi e custodia conservata:** impedisce che risultati e comandi di A diventino artificialmente risultati/comandi di B. Nessuna modifica al PHY LoRa congelato, MAC o driver.

**Criterio di successo:** attribuzione esatta nei test sintetici; sul campo soltanto dopo aver osservato le effettive trasmissioni, consegne e classificazioni.
