# UC-236 — Stanze tematiche territoriali GeoTopic

Stato: proposta 21 ottobre 2026, non implementata.

## Problema e attori
Una classe vuole leggere aggiornamenti su robotica relativi al checkpoint pubblico Rometta–Venetico, anche se i due laboratori non sono collegati. Attori: editori autorizzati, utenti che scelgono volontariamente una stanza, cache scolastiche e studenti con nodi store-and-forward. La zona è un'etichetta pubblica di servizio, non la posizione della persona.

## PollicinoNet e trasporti
La selezione è una congiunzione di tema, zona grossolana e finestra di validità. LoRa porta ID opachi, hash e annunci brevi; BLE scambia inventari; Wi-Fi trasferisce documenti e post; Internet è opzionale; laptop o USB permettono trasporto fisico. Oggetti vincolati a room_id, topic_id, zone_id, publisher_id, event_id, sequence, expiry e hash; firme per gli editori.

## Prove software
Simulare tre zone, tre stanze, otto relay, pubblicazioni ritardate e utenti offline. Inserire duplicati, annullamenti, iscrizioni ritirate, messaggi di zona sbagliata, firme non valide e scadenze con orologi incerti. Risultato verificabile: nulla appare in una stanza errata; nessun evento scaduto è presentato come attuale. Misurare messaggi utili, falsi recapiti, byte, ritardi e rifiuti.

## Hardware
Due cache PC, 6–8 schede e due checkpoint scolastici autorizzati. Misurare invii effettivi, ricezioni, contatti e accettazione applicativa. Non dedurre copertura geografica senza misure.

## Privacy e difficoltà
Niente GPS, indirizzi di casa o cronologie personali. Identificativi opachi, scadenza breve, controllo di accesso e cifratura dove serve. Un relay che trasporta un evento non prova la presenza dell'utente nella zona. Difficoltà medio-alta.

## Novità
UC-083 copre il topic, UC-142 il checkpoint, UC-102 il groupcast. Qui si verifica insieme tema, ambito pubblico e validità su connessioni intermittenti, senza modificare il PHY LoRa.

Riferimenti: https://doi.org/10.1145/3529978 ; https://www.rfc-editor.org/rfc/rfc9171.html .
