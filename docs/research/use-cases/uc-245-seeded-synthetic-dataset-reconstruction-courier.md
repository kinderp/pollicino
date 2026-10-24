# UC-245 — Dataset sintetici ricostruibili da ricette compatte

**Stato:** proposta documentale 23 ottobre 2026, integrata nel catalogo il 24 ottobre. Non implementata; nessuna misura radio. **Difficoltà:** medio-alta.

## Problema e attori
Tre laboratori scolastici, ad esempio Messina, Rometta e Venetico, devono utilizzare lo stesso dataset **artificiale** per studiare AI, IoT e analisi statistica. Trasferire ogni volta l'intero archivio via collegamenti intermittenti sarebbe costoso. Un docente editore mette a disposizione una ricetta deterministica; due computer isolati la eseguono localmente; cache e relay studenteschi consegnano gli identificativi e gli eventuali blocchi mancanti.

## Perché PollicinoNet
Le opportunità di contatto sono brevi e il nodo destinatario potrebbe avere tempo di calcolo ma pochi byte trasferibili. `DISCOVERY` annuncia l'artefatto, `EXACT` richiede verifica byte per byte del risultato rigenerato. La generazione resta applicativa: non si cambiano MAC o PHY LoRa. In caso di ricostruzione difforme si effettua **fallback al trasferimento esatto**.

## Bearer
- **LoRa:** piccoli annunci, identificativo della ricetta e disponibilità, senza farvi viaggiare dataset grandi.
- **BLE:** confronto di inventari e manifest locali.
- **Wi-Fi/Internet:** manifest firmati, generatori autorizzati e blocchi verificati quando disponibile.
- **USB / trasporto fisico:** dataset e modelli grandi nei contatti fra laboratori senza backhaul.

## Contratto minimo
Manifest firmato con dataset_id, generator_id e versione *pinnata*, hash degli asset e del generatore autorizzato, algoritmo RNG/versione, seed, parametri, schema, ordine delle colonne, serializzazione canonica, byte attesi, SHA-256 completo, limiti CPU/RAM/tempo e politica di fallback. Il digest radio abbreviato è un indizio di scoperta, **non** una prova d'identità. Non scaricare né eseguire codice arbitrario da annunci.

## Cosa provare senza hardware
Generare 100.000 righe sintetiche in due ambienti isolati e confrontare SHA-256. Iniettare seed errato, schema differente, drift di versione, output incompleto, CPU esaurita, generatori assenti e trasferimenti interrotti. Confrontare (A) file compresso, (B) ricetta + calcolo, (C) ricetta + recupero esatto, includendo **anche** il costo di installare il generatore; usare dati pseudo-casuali difficilmente comprimibili come controllo negativo. Criterio: dichiarare `EXACT` esclusivamente quando lunghezza e digest del file canonico coincidono.

## Quali prove fisiche
Due PC offline, 4–6 schede LoRa e checkpoint autorizzati. Registrare TX realmente eseguiti e RX indipendenti, byte su ciascun bearer, tempi dal primo annuncio alla verifica dell'artefatto, CPU/RAM del ricevente. L'energia va misurata separatamente con strumenti appropriati. Nessuna stima di throughput o copertura prima dei test.

## Privacy, sicurezza e limiti
Usare solo dati sintetici, firme, hash integrali, limiti di risorse, licenze e sandbox per generatori pre-approvati. Non sostituire un output semanticamente simile a una copia `EXACT`. Evitare segreti e dataset personali.

## Anti-duplicati
UC-004 distribuisce artefatti; UC-061 riusa risultati; UC-104 distribuisce delta; UC-130 deduplica chunk; UC-187 ripete protocolli. **Questo caso misura il compromesso verificabile fra rigenerazione deterministica e trasporto dei byte**, con fallback obbligatorio.
