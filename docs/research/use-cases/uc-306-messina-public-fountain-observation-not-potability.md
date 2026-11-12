# UC-306 — Fontanelle e sorgenti pubbliche: osservare disponibilità senza dichiarare potabilità

**Stato (12 novembre 2026):** proposta didattica documentale, nessun test né sopralluogo eseguito. Difficoltà **medio-alta**. PHY LoRa congelato, MAC, firmware e driver invariati.

## Problema concreto
Fra comuni costieri e frazioni dell'entroterra messinese, una piccola mappa partecipata può raccogliere osservazioni su **punti d'acqua pubblici**: il getto era visibile? la postazione era accessibile all'osservatore? il rilievo è stato realmente svolto? Una segnalazione vecchia o mai verificata può essere scambiata per informazione attuale. Soprattutto, **acqua visibilmente presente o limpida non significa potabile**. La mappa scolastica non deve attestare idoneità al consumo né sostituire gestori o autorità sanitarie.

## Attori e scenario Messina
Docenti/revisori, gruppi di osservazione supervisionati, 3 punti fittizi `F-01/F-02/F-03`, un checkpoint, PC di laboratorio e 4–6 relay di prova. Una possibile estensione comprende **solo punti pubblici effettivamente autorizzati** in aree come Rometta, Saponara e Venetico; nessuna fontanella reale è stata qui censita o dichiarata funzionante. Nessuna visita individuale obbligatoria o registrazione degli itinerari studenti.

## Perché PollicinoNet
In zone prive di connettività continuativa la scheda può conservare brevi osservazioni, distinguere **ora dell'osservazione** e **ora della consegna**, e inoltrarle al revisore quando appare un contatto. La rete opportunistica non deve cancellare conflitti fra osservazioni, attribuire sicurezza sanitaria o elevare una constatazione visiva a dato ufficiale.

- **DISCOVERY:** ID della postazione pubblica, disponibilità di un'osservazione breve e stato della revisione.
- **EXACT:** record firmato/autorizzato, timestamp con incertezza, protocollo e hash dell'eventuale evidenza.
- **SEMANTIC:** `FLOW_OBSERVED`, `NO_FLOW_OBSERVED`, `NOT_VISITED`, `NOT_ASSESSABLE`, `STALE`; **mai `POTABLE`** per inferenza.

## Bearer possibili
- **LoRa:** osservazioni minimali tipizzate o annunci, solo se l'adapter supporta il payload e il budget radio lo permette.
- **BLE:** raccolta locale e verifica presso un nodo scolastico.
- **Wi-Fi/LAN/Internet:** schede descrittive, revisioni e foto prive di persone se consentite.
- **USB/SD e trasporto fisico:** log completi o evidenze autorizzate fra scuole; nessuna scheda deve essere installata nell'impianto idrico.

## Prova software immediata (non eseguita)
Simulare **3 fontanelle fittizie e 18 osservazioni** con finestre orarie inventate. Inserire: assenza di sopralluogo, postazione non valutabile, getto visibile, nessun getto osservato, notifica tardiva, due osservazioni in conflitto, verbale ritirato, hash evidenza non corrispondente, data troppo vecchia e autore non autorizzato. Confrontare un ingenuo `last-message-wins` e una policy di **validità/revisione con esposizione dell'incertezza**.

**Metriche:** numero di stati mostrati con fonte e scadenza corretti; segnalazioni obsolete erroneamente presentate come attuali (obiettivo 0 nelle fixture); conflitti conservati; byte di annuncio e tempo dalla revisione alla disponibilità presso la cache virtuale. Niente conclusioni su acqua reale o qualità.

**Criteri di accettazione:** 
1. `NOT_VISITED` e `NOT_ASSESSABLE` non equivalgono a `NO_FLOW_OBSERVED`.
2. Una vecchia osservazione positiva non prevale su una revisione successiva solo perché consegnata dopo.
3. Nessun segnale sensoriale, colore dell'acqua o fotografia abilita un attributo di potabilità; eventuale comunicazione ufficiale è un **link separato** alla fonte competente, da verificare.
4. Stati dubbi, confliggenti o scaduti restano etichettati come tali.
5. Pubblicare solo luoghi autorizzati e dati verificati, senza facce, targhe, metadati EXIF con posizioni personali.

## Hardware necessario e misure reali
Per prima cosa **4 schede e 2 PC** in laboratorio con 18 record fittizi, spedizione differita e ricevute applicative. In una fase distinta, previo permesso, un docente può verificare il metodo di osservazione su **uno o due soli punti pubblici** senza collegare sensori a rubinetti, condotte o reti potabili e senza consumare l'acqua per testarla. Per prove di portata o qualità servirebbero strumenti, metodi, competenze e autorizzazioni specifiche: sono **fuori ambito**.

Verificare i limiti radio applicabili prima delle TX. Solo misure su schede reali possono documentare ricezioni, consegne, energia, airtime o copertura fra checkpoint.

## Privacy, sicurezza, responsabilità
Solo punti pubblici, granularità territoriale appropriata e osservazioni supervisionate. Mai profili di abitudini, check-in personali o percorsi di minori. Retention limitata, canale per correzioni e diritto di ritiro nei limiti dichiarati. Nessun uso per emergenze, idoneità igienica, decisioni sanitarie o raccomandazioni di bere acqua. Mostrare sempre **«osservazione didattica; potabilità non verificata»**.

## Anti-duplicazione
**UC-191** allinea contatori di portata, **UC-146** riguarda l'irrigazione, **UC-171** la qualità delle acque costiere, **UC-185** distingue non-rilevamento da mancata osservazione, **UC-049** comunica condizioni di percorso. **UC-306** è una micro-app di **osservazioni pubbliche su disponibilità, revisione e obsolescenza di un punto d'acqua**, con confine sanitario esplicito; riusa i principi tecnici anziché duplicarli.

Contesto normativo (non attestazione delle fontanelle considerate): Commissione europea, direttiva (UE) 2020/2184 sull'acqua potabile: https://environment.ec.europa.eu/topics/water/drinking-water_en
