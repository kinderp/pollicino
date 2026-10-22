# UC-241 — Mazzi didattici offline con ripasso dilazionato e progresso locale privato

**Stato:** proposta documentale del 22 ottobre 2026; non implementata. **Difficoltà:** media.

## Problema e storia d'uso
Una classe di Informatica prepara schede di ripasso su C, Python e reti. Gli studenti studiano offline anche quando il materiale viene aggiornato in un altro laboratorio. La distribuzione del materiale **non deve obbligare a distribuire** gli orari di studio, gli errori individuali o il profilo di apprendimento.

**Scenario Messina:** un laboratorio pubblica la versione 3 del mazzo; relay volontari tra checkpoint scolastici di Messina, Rometta e Venetico ne portano l'annuncio, mentre PC scolastici sincronizzano il contenuto completo quando incontrano Wi-Fi o un disco USB. Ogni studente mantiene sul proprio dispositivo la pianificazione di ripasso.

## Attori e perché PollicinoNet
Docente-editore, studenti-lettori, cache scolastiche e relay. PollicinoNet permette di trasportare manifest di versioni e richieste anche senza un server sempre raggiungibile; il contenuto può attraversare mezzi differenti senza cambiare hash. Componenti applicativi proposti: **deck manifest** (deck_id, version, content_hash, lingua, licenza, expiry, issuer), carte e risorse multimediali, stato SRS esclusivamente locale.

## Bearer
- **LoRa:** annuncio della nuova versione e identificativo/hash corto; non veicolare cronologie di studio, audio o grandi documenti.
- **BLE/Wi-Fi/LAN:** pacchetto completo con esercizi, immagini e collegamenti a fonti Raiatea; **Internet** come opportunità aggiuntiva.
- **USB/SSD/trasporto fisico:** trasferimento del pacchetto da un laboratorio a un altro, previo controllo dell'integrità.

## Esperimento software immediato
Due client scollegati, una cache e mazzi sintetici (nessun rendimento scolastico reale). Pubblicare v1 e v2 con una carta ritirata, una corretta e una aggiunta. Verificare: importazione con hash/firma; migrazione esplicita degli identificativi di carta; calendario SRS locale che non si perde al cambio versione; versione revocata non considerata automaticamente valida; risorsa Raiatea mancante marcata **in attesa** e non inventata; doppio trasporto dello stesso aggiornamento senza duplicare le carte. Testare computer offline dopo un riavvio e conflitto tra due editori non autorizzati. Prodotto FSL: piccolo client Python/web con manifest, importatore, card viewer accessibile, test pytest e specifiche di accettazione.

## Hardware reale necessario
La funzione didattica si dimostra senza LoRa. Per il confronto reale bastano 4–6 schede e due PC isolati in aule autorizzate: misurare tempo tra annuncio e arrivo del pacchetto, integrità, bytes su ciascun bearer e successiva apertura offline. Se trasportato da studenti, nessuna registrazione degli spostamenti personali. Nessuna promessa di throughput radio.

## Privacy e sicurezza
Il calendario SRS, le risposte e gli errori **rimangono sul dispositivo**, senza telemetria predefinita; nessun registro nominativo passa nei relay. Eventuali aggregati di classe richiedono finalità/autorizzazione definite e soglie che non consentano identificazione indiretta, specialmente con pochi studenti. Materiali firmati, hash e licenze verificate, autori autorizzati, sandbox per eventuali esercizi eseguibili e contenuti accessibili.

## Differenza rispetto al catalogo
UC-229 certifica che una **lezione sia eseguibile**; UC-054 porta consegne e feedback; UC-192 cura derivati accessibili; UC-083 avvisa degli aggiornamenti. **UC-241** tratta la sincronizzazione di **mazzi di ripasso versionati** preservando il progresso individuale solo in locale. Nessuna modifica del PHY LoRa.

Riferimenti: https://www.w3.org/TR/WCAG22/ ; https://www.rfc-editor.org/rfc/rfc9171.html .
