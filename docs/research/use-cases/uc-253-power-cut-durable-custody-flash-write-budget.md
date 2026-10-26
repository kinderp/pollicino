# UC-253 — Custodia durevole dopo riavvio con budget di scritture

**Stato:** proposta documentale del 26 ottobre 2026. Nessun test eseguito, nessuna prova fisica. **Difficoltà:** medio-alta (simulatore); alta (implementazione robusta su dispositivi embedded).

## Problema concreto e user story
Un relay nello zaino riceve una capsula, conferma al mittente di averne preso in carico la conservazione, ma poi viene spento per ricaricare la batteria. Se l'ack è stato inviato prima del salvataggio durevole, dopo il riavvio il relay potrebbe non possedere più il messaggio. Scrivere ogni piccolo cambiamento in memoria persistente, però, può aumentare latenza, consumo e usura della flash. Bisogna misurare e governare questo compromesso, senza confondere un semplice «ricevuto» con la responsabilità di custodia.

**User story:** «Come studente che presta volontariamente il nodo, voglio poterlo spegnere e riaccendere senza che un messaggio già dichiarato custodito sparisca silenziosamente, e senza scrivere inutilmente nella memoria a ogni contatto».

## Attori, nodi e scenario Messina
Mittente applicativo, relay con storage persistente, successivo relay, destinatario/verificatore e docente. Primo test con due PC e 4 schede sul banco; successivamente checkpoint scolastici autorizzati a Rometta, Venetico e Villafranca, senza registrare tragitti individuali. I relay sono volontari: l'interruzione locale della partecipazione resta prioritaria (UC-217).

## Perché PollicinoNet e bearer
La separazione temporale fra «ricevo adesso» e «consegno al prossimo incontro» rende necessaria la persistenza dei bundle. **LoRa** porta capsule piccole e ricevute compatte secondo le capacità e i budget già supportati; **BLE** e **Wi-Fi** possono essere usati per inventari o trasferimenti più grandi; **Internet** sincronizza presso gateway; **USB o supporto fisico** recuperano log e oggetti in laboratorio. Il trasporto non certifica da solo la custodia persistente.

## Contratto applicativo e invarianti
Distinguere stati RECEIVED_VOLATILE, DURABLY_STORED, CUSTODY_ACKED, FORWARDED e APPLICATION_ACCEPTED. Ogni oggetto ha ID e hash; gli ack di custodia sono autenticati e legati all'esatto oggetto e all'epoca di stato.

- Non emettere CUSTODY_ACKED prima che i dati essenziali e l'indice di recupero risultino effettivamente persistiti secondo il contratto scelto.
- Dopo un riavvio, un oggetto dichiarato custodito deve essere recuperabile e verificabile oppure deve emergere un errore esplicito; mai dichiarare successo silenzioso.
- La replay protection e la deduplicazione devono sopravvivere ai riavvii almeno per la finestra di validità dichiarata. Una ricevuta di custodia non è una ricevuta di accettazione applicativa (UC-221).
- Limitare le scritture: journaling, batching e snapshot sono alternative da **confrontare**, non risultati presunti; quando il budget è esaurito, il relay può rifiutare nuova custodia.

## Esperimenti software subito
Modellare una coda con journal persistente e un simulatore di arresto/riavvio che interrompa l'esecuzione dopo ogni passaggio critico: ricezione, scrittura record, flush, indice, ack, dedup, snapshot. Confrontare due politiche: (A) conferma solo dopo persistenza sincrona; (B) raggruppamento delle scritture **senza promettere custodia prima del flush**. Iniettare record tronchi, hash errati, riordino e duplicati. Eseguire test a proprietà su sequenze di eventi sintetici.

Metriche software: numero di bundle già confermati ma non recuperabili (obiettivo **zero nel modello dichiarato**), amplificazione delle scritture, byte scritti per oggetto, latenza della ricevuta, spazio occupato, tempo di recupero e oggetti rifiutati. Non convertire la stima di scritture in anni di vita della flash senza evidenze specifiche.

## Prove hardware necessarie
Identificare memoria realmente disponibile e comportamento del filesystem/driver **senza modificare il PHY LoRa congelato**. Usare 2–4 schede, storage previsto dal progetto e logger USB; effettuare riavvii normali tramite alimentazione controllata entro specifica, non cortocircuiti o manovre elettriche rischiose. Verificare oggetti e ricevute prima/dopo riavvio, consumo e latenza; documentare i limiti di osservabilità delle scritture reali, evitando di proclamare endurance senza campagna prolungata. In fase di campo misurare TX/RX indipendenti e consegna applicativa.

## Privacy, sicurezza, difficoltà e non-duplicazione
Cifrare o minimizzare i contenuti locali sensibili; niente nome, GPS, orari nominativi o percorsi di studenti; eliminazione controllata a fine trial. Verificare firme e hash, gestire errori di storage, impedire ack forgiati e riuso di ID. UC-172 tratta compattazione dei log, UC-184 il salvataggio d'emergenza, UC-233 la ripartenza simultanea e UC-252 il bilancio energetico di una giornata; **qui la proprietà nuova è che una promessa di custodia sopravviva al riavvio con un budget di scritture misurabile**. La prova non modifica MAC, driver o firmware radio.
