# UC-304 — Contatti brevi e simultanei ai checkpoint scolastici: chi viene servito davvero?

**Stato (12 novembre 2026):** nuova proposta di documentazione; **nessun test software/fisico eseguito**. Difficoltà **medio-alta**. Non cambiare PHY LoRa congelato, MAC, firmware o driver.

## Problema concreto
Quando più relay volontari si trovano vicino a un checkpoint per pochissimi secondi, la semplice rilevazione della presenza radio non significa che il checkpoint riesca a scoprire, negoziare e accettare tutti gli oggetti. Una politica che prende sempre il primo nodo può inoltre lasciare senza servizio gli altri dispositivi di prova. Non serve affatto osservare gli studenti all'uscita: la situazione può essere **riprodotta in laboratorio con schede statiche e contatti applicativi abilitati per intervalli brevi**.

**Domanda misurabile:** con finestre identiche e un numero noto di oggetti, quali strategie massimizzano le **ricevute applicative EXACT entro la fine del contatto** senza superare budget radio/cache o favorire sempre lo stesso dispositivo sintetico?

## Attori e nodi; scenario Messina
Un checkpoint fisso scolastico, 6–10 relay virtuali (poi 4–6 schede di laboratorio), un PC collector, un docente responsabile e un destinatario applicativo. Nel modello i checkpoint etichettati `Rometta`, `Villafranca`, `Venetico` e `Spadafora` sono **nomi di scenari, non collegamenti radio verificati**. Un eventuale coinvolgimento futuro degli studenti è facoltativo, supervisionato e senza misura degli ingressi, dei percorsi o della presenza.

## Perché PollicinoNet
L'incontro opportunistico fra portatore e checkpoint è breve; store-and-forward lascia in custodia gli oggetti non consegnati e li ritenta in un contatto successivo. Separare discovery, verifica EXACT e trasferimento permette di contabilizzare il **tempo perso nella negoziazione** rispetto agli oggetti effettivamente utili. Il progetto confronta *politiche applicative*, non introduce nuove modalità radio.

- **DISCOVERY:** solo disponibilità/necessità compatte e autorizzate, senza identità persistenti.
- **EXACT:** manifest dell'oggetto, integrità e ricevuta dell'applicazione; nessuna consegna dedotta da un RSSI o da un handshake.
- **SEMANTIC:** classe di domanda (`lesson-pack`, `sensor-summary`, `exercise-only`), mai informazioni personali.

## Bearer possibili
- **LoRa:** capsule di annuncio o controllo soltanto se già supportate dall'adapter e compatibili con il budget radio; niente file voluminosi né raffiche aggressive.
- **BLE:** scoperta/handoff vicino al checkpoint, quando la capability esiste.
- **Wi-Fi/LAN/Internet:** scambio dei manifest estesi, contenuti e ricevute tramite connessioni autorizzate.
- **USB/SD / trasporto fisico:** alternativa per dati voluminosi oppure ritiro dei log; conteggiare distintamente il contatto fisico.

## Prova software immediata (non eseguita)
Simulatore Python a eventi discreti, **8 relay**, **40 oggetti fittizi** e finestre di **5/15/30 secondi puramente sintetiche**; seminare ritardi di scansione, handshake interrotto, contatto troppo breve, ricevute mancanti, backlog, duplicati e differenze fra capacità dei bearer. Stesso workload e stesso seed per tre bracci:
1. `FIRST_SEEN`: il checkpoint serve il primo relay annunciato;
2. `BOUNDED_ROUND_ROBIN`: turno di servizio limitato per dispositivo virtuale;
3. `NEED_FIRST`: riconcilia solo gli oggetti richiesti e verificabili entro la finestra.

**Metriche:** oggetti EXACT con ricevuta entro contatto / oggetti richiesti e ammessi; contatti terminati senza consegna; tempo discovery→ricevuta; byte di controllo rispetto ai byte utili; distribuzione delle opportunità **tra dispositivi sintetici**, mai classifica studenti; stato `UNKNOWN` per log incompleti. Non calcolare un PDR radio da durate di contatto inventate.

**Criteri di accettazione futuri:**
- Un `DISCOVERED` non diventa `DELIVERED` senza verifica EXACT e ricevuta applicativa.
- Contatto interrotto e log mancante producono `INCOMPLETE`/`UNKNOWN`, non successo.
- Nessuna strategia supera quote di custodia, limite messaggi per contatto o permessi.
- L'analisi di equità considera solo ID temporanei dei nodi di prova e non persone.
- Ogni confronto usa gli stessi contatti sintetici; non promette vantaggi su siti fisici.

## Prova fisica indispensabile
Iniziare **con 4–6 schede e due PC in laboratorio**, checkpoint statico e gate software che apre/chiude sessioni con durate *misurate*, senza spostare persone. Log indipendenti per handshake, TX/RX effettivamente osservabili e ricevute dell'app. Alternare l'ordine dei bracci e verificare prima firmware/configurazione già disponibile, antenna, limiti regionali/normativi e budget di airtime. Non provocare collisioni, affollamenti veri o interferenze.

Solo dopo: due postazioni scolastiche autorizzate nella provincia di Messina con contatti di prova, se il collegamento radio viene **misurato**, non presunto. Una finestra simulata non misura copertura, PDR, throughput, latenza, consumo o prestazioni di BLE su telefoni reali.

## Privacy, sicurezza, non obiettivi
Divieto di registrare ora di ingresso/uscita, Bluetooth MAC personali, presenze o spostamenti; usare dispositivi scolastici, ID per campagna, opt-out e retention breve. Nessuna prova durante la vera uscita di una scuola; nessun invio a canali di emergenza reali. Budget e limiti applicativi impediscono abuso del canale condiviso.

## Distinzione dagli UC esistenti
**UC-233** studia il *rientro dopo un blackout* e le code; **UC-265** isola TX contemporanee e ricezione radio; **UC-188** la fattibilità di un singolo payload; **UC-095** il budget dei relay. **UC-304** confronta *la selezione delle sessioni applicative quando molti contatti sono simultanei ma brevissimi*, con ricevute end-to-end e fairness fra nodi fittizi. Non è una misura radio.

Riferimento di contesto, senza dichiarazione di conformità BPv7: https://www.rfc-editor.org/rfc/rfc9171.html
