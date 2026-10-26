# UC-255 — Beacon territoriale GeoTopic autenticato, anche offline

**Stato:** proposta documentale del 26 ottobre 2026. Nessun software/hardware validato. **Difficoltà:** alta per il modello di fiducia, media per un primo simulatore.

## Problema concreto e user story
In una scuola un client scopre tramite BLE il suggerimento «stanza dell'istituto». Un dispositivo vicino potrebbe però trasmettere un nome identico, un vecchio identificativo oppure copiare un annuncio valido da un altro luogo. **La prossimità radio non è autorità per dichiarare un luogo GeoTopic**, e un annuncio autentico ricevuto altrove non costituisce prova affidabile della presenza fisica dell'utente.

**User story:** «Come studente volontario, voglio scoprire una stanza del checkpoint scolastico e sapere se l'annuncio corrisponde a un luogo approvato, anche senza Internet, senza registrare dove mi trovo e senza che un falso beacon ottenga privilegi».

## Attori e contesto Messina
Registro GeoTopic autorizzato (UC-250), gestore del checkpoint, uno o più beacon di prova, smartphone/PC client, cache e relay mobili. Esempio: postazione temporanea autorizzata in un laboratorio a Venetico e altra a Rometta; stessi topic di esempio ma ID di luogo differenti. Tutti i nomi degli istituti nel prototipo sono fittizi; non trasmettere nomi o dati dei partecipanti.

## Ruolo PollicinoNet e bearer
**BLE** può annunciare un riferimento breve, mai un'autorizzazione implicita; il manifest firmato completo può essere recuperato tramite BLE GATT/scan response ove possibile, **Wi-Fi** o **Internet**. **LoRa** può diffondere solo hash/epoch compatti di manifest pubblici secondo le capacità effettive delle schede; **QR/USB o trasporto fisico** portano manifest firmati in partizioni completamente isolate. Store-and-forward rende disponibile un manifest dopo un incontro differito, senza attribuire al relay il potere di emetterlo. Le dimensioni reali degli advertising BLE e dei payload LoRa vanno verificate prima di decidere il formato binario.

## Contratto e proprietà
Il registro autorizza un place_id canonico e il materiale pubblico del gestore. Un manifest firmato associa place_id, issuer, epoch, digest del contenuto autorizzato, validità e chiave usata; il beacon trasmette un hint corto con il digest/identificativo necessario a recuperarlo.

- Firmare e verificare il manifest rispetto a una radice di fiducia previamente installata; un nome in chiaro o l'RSSI non bastano.
- Su chiave revocata, epoca non riconosciuta, clock incerto o manifest assente, presentare lo stato **NON_VERIFICATO** oppure NON_ATTUALE; non creare una nuova stanza ufficiale per deduzione.
- Non confondere firma valida del manifest con prova di posizione, assenza di relay malevoli o diritto di entrare in un gruppo privato. Una trasmissione BLE può essere registrata, riprodotta o inoltrata da terzi.
- Non usare il beacon per abilitare accessi sensibili o «proof-of-presence» senza un protocollo separato, esplicito e valutato.

## Test software subito
Tre luoghi fittizi, due cache disconnesse e un verificatore locale. Iniettare beacon contraffatti, firme errate, replay di manifest vecchi, rotazione di chiavi, duplicati, alias in conflitto, clock inaccurato, recupero del manifest in ritardo e trasporto attraverso più bearer. Confrontare client che «si fidano del nome» con client che verificano i manifest. Obiettivo di accettazione del prototipo: **zero promozioni di identità non autorizzata a luogo ufficiale** per i casi sintetici; segnalare sempre gli stati incerti.

Misure: tasso di falsi accetti nei test artificiali, casi non verificabili, latenza del recupero, byte trasportati sui diversi bearer, conflitti rilevati e numero di informazioni personali raccolte (obiettivo zero).

## Prova fisica necessaria
Due beacon BLE configurabili di prova, smartphone o PC compatibili, 4 schede LoRa se e quando l'adapter applicativo è pronto, due checkpoint autorizzati. Ripetere discovery reale, aggiornamento manifest e perdita del collegamento; misurare i payload, RSSI solo a fini diagnostici locali e tempi di verifica. Test di attacco soltanto su dispositivi di laboratorio propri, con identificativi artificiali e senza impersonare beacon reali. Non assumere che ogni scheda LoRa disponga anche di BLE.

## Privacy, sicurezza e non-duplicazione
Nessun ID stabile di scanner, log di scansioni degli studenti, profilo di movimento, GPS, identificatori privati o tracce nominative. Conservare solo log di esito aggregati e temporanei; rispetto delle regole di opt-in/STOP (UC-217). UC-250 governa il **nome** ufficiale, UC-247 la vita delle room BLE, UC-248 la rilevanza locale e UC-067 i servizi nominati: **UC-255 riguarda l'autenticità degli annunci fisici di scoperta e i fallimenti di fiducia offline**, senza promettere una prova di presenza. Non modifica PHY/MAC/driver.
