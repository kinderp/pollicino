# UC-238 — Bacheca offline accessibile con simboli, testo e voce

Stato: proposta didattica 21 ottobre 2026, non implementata. Non è un sistema di emergenza.

## Problema e attori
Due aule vogliono inviare richieste non urgenti («materiale pronto», «possiamo iniziare?», «serve una spiegazione») anche in assenza di Internet. Una semplice interfaccia a pittogrammi, testo leggibile e sintesi vocale locale consente modalità di interazione differenti senza raccogliere dati di salute. Attori: docenti, partecipanti volontari, due client locali, gateway e relay degli studenti.

## PollicinoNet e bearer
L'oggetto contiene intent_code, dictionary_version, recipient_id, sequence, expiry e ricevuta. LoRa trasporta intenti brevi e ack; BLE permette scambi vicini; Wi-Fi distribuisce dizionario e simboli; Internet è opzionale; QR/USB possono portare dizionari aggiornati. La lettura vocale avviene sul client, non via LoRa.

## Test software subito
Preparare sei intenti di laboratorio sintetici e due interfacce web isolate, accessibili da tastiera, con testo alternativo e TTS locale. Simulare otto relay, duplicati, messaggi in ritardo, versione dizionario incompatibile, audio non disponibile e ACK anticipato. Invarianti: significato di ogni codice vincolato alla versione, duplicati non letti due volte, contenuti scaduti segnalati come non attuali. Verificare focus, etichette, leggibilità e screen reader sul target reale; i test automatici non bastano per attestare accessibilità.

## Prova fisica
Due tablet/PC, 4–6 schede LoRa e due postazioni scolastiche. Registrare trasmissioni, consegne, latenza fino a visualizzazione/lettura, duplicati e perdita delle ricevute; testare le funzionalità di accessibilità con revisore umano volontario.

## Privacy/sicurezza e difficoltà
Niente diagnosi, nomi di minori o log dei bisogni personali. Pseudonimi per le demo, messaggi cifrati se privati, autenticazione del destinatario, breve conservazione. Nessuna promessa di risposta immediata; non usare per richiesta di soccorso. Difficoltà media per demo, medio-alta per l'usabilità con tecnologie assistive.

## Novità
UC-192 riguarda pacchetti didattici accessibili, UC-106 bollettini, UC-023 posta privata generica. UC-238 è una **interfaccia interattiva multimodale** per intenti non urgenti su rete intermittente. PHY congelato invariato.

Riferimenti: https://www.w3.org/TR/WCAG22/ ; https://w3c.github.io/adapt/symbols/ .
