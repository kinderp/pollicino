# UC-249 — Micro-osservazioni IoT compattate con dizionari di schema verificabili

**Stato:** proposta del 24 ottobre 2026, nessuna implementazione o misura radio. **Difficoltà:** medio-alta (compatibilità, significato, fallback).

## Problema concreto
Quattro scuole registrano piccole osservazioni di temperatura, umidità e stato di un orto. Ogni osservazione JSON completa ripete molti nomi di campo: su bearer a capacità limitata conviene confrontare un formato binario compatto e un dizionario **già condiviso**. Un ricevitore con la versione sbagliata non deve scambiare una misura di umidità per una di temperatura.

## Attori e rete
Sensore fisso autorizzato, gateway applicativo, 4–8 schede LoRa come relay store-and-forward di riepiloghi piccoli, laboratorio e revisore. Prima test con dati fittizi in due classi; poi postazioni autorizzate a Venetico, Rometta e Messina.

## Perché PollicinoNet
`DISCOVERY` segnala la versione di schema; `EXACT` protegge il manifest e gli eventuali blocchi di storico. I payload radio vengono scelti dal **livello applicativo** rispettando limiti e budget del bearer; niente modifica al PHY congelato né ipotesi che tutti i messaggi possano contenere qualunque lunghezza.

## Bearer
- **LoRa:** unicamente osservazioni compatte che rientrano nei limiti dell'attuale trasporto, identificativi di dizionario e richieste minime.
- **BLE:** scambio locale di schemi mancanti quando consentito.
- **Wi-Fi / Internet:** manifest firmati, dizionari, storici e dataset completi.
- **USB / trasporto fisico:** riuso delle definizioni di schema e storici senza collegamento.

## Contratto dei dati
`schema_id` e versione/hash completo nel manifest di fiducia, tipo, unità di misura, intervallo, risoluzione/arrotondamento esplicito, timestamp con qualità, calibrazione e provenienza del sensore. Il pacchetto può contenere alias breve del dizionario soltanto se il ricevente lo ha già associato in modo verificabile al manifest esatto. Nessun decode cieco; stato `UNKNOWN_SCHEMA` e richiesta di schema tramite bearer più ricco. Non chiamare `EXACT` una rappresentazione con perdita: specificare un'eventuale quantizzazione come nuovo dato derivato con provenienza.

## Esperimenti senza radio
Produrre 10.000 osservazioni sintetiche, confrontare (A) JSON canonico, (B) CBOR standard, (C) dizionario tipizzato versionato. Misurare byte codificati e CPU di encoding/decoding; testare schema errato, unità invertite, float non finiti, truncation, timestamp incerto, versioni miste e payload corrotti. Il decoder deve rifiutare o marcare `UNKNOWN` prima di presentare valori sbagliati. Criteri: round-trip semantico corretto per ogni test valido, nessun decode di schema ignoto, nessun superamento dei limiti di payload configurati.

## Prove hardware
4–8 schede verificate (UC-206), 2 ricevitori di riferimento e 2 sensori fissi o simulatori hardware. Log indipendenti di TX/RX, dimensione effettiva dei payload, ritrasmissioni, tempo di riconciliazione di schema e correttezza della misura finale. Solo dopo misure reali confrontare airtime, affidabilità ed energia, rispettando le condizioni radio applicabili.

## Privacy e sicurezza
Nessun dato personale, identificativi dei sensori non riconducibili a studenti, autenticazione del dizionario/schema, integrità applicativa e replay guard. I dati sensibili su luoghi privati non sono pubblicati; riportare incertezza e qualità metrologica.

## Anti-duplicati
UC-003 è il trasporto sensori; UC-115 mappa ontologie; UC-117 valida qualità; UC-135 migra schemi; UC-230 prova adapter fra bearer; UC-245 rigenera dataset. **UC-249 verifica invece un formato realmente compatto di singoli fatti tipizzati con schema/versione condivisi e rifiuto sicuro dello schema ignoto.**
