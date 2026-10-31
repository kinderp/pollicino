# UC-268 — Contatti LoRa mancati per finestre di ascolto non coincidenti

**Stato:** proposta documentale del 31 ottobre 2026. Nessuna misura fisica o funzionalità implementata. Il PHY LoRa congelato, il MAC, i driver e il firmware non sono modificati. **Difficoltà:** medio-alta.

## Problema risolto e user story

Due schede possono trovarsi in un'area in cui il collegamento radio funzionerebbe, ma non rilevarsi perché una trasmette mentre l'altra non è in ascolto. Se misuriamo soltanto i messaggi ricevuti potremmo dichiarare inesistente un contatto che invece era **potenzialmente utilizzabile**. Per una rete studentesca store-and-forward la mancata scoperta di un incontro breve può ritardare una consegna anche senza perdita radio nel senso abituale.

**User story:** come responsabile del testbed voglio distinguere l'assenza fisica di opportunità radio dall'assenza di sovrapposizione delle finestre di trasmissione/ascolto, per scegliere esperimenti sostenibili senza inventare copertura o cambiare il PHY.

## Attori, nodi, contesto messinese

Docente coordinatore; nodi A e B con configurazione documentata; ricevitore di riferimento R e collector indipendente; 4–6 schede LoRa e due PC; in seguito checkpoint scolastici fissi e autorizzati a Rometta, Venetico, Villafranca o Messina. Un relay volontario trasportato da uno studente può custodire i riepiloghi dell'esperimento e inoltrarli quando incontra una cache; **non raccogliere né inferire il percorso dello studente**. Iniziare con postazioni fisse: i movimenti non controllati renderebbero difficile distinguere cause.

## Perché PollicinoNet e bearer

Lo store-and-forward dipende da contatti intermittenti: non basta che la portata teorica sia sufficiente; occorre che i nodi **si scoprano**. PollicinoNet conserva identificativi di campagna, eventi di discovery, evidenze e report, senza equiparare un beacon ricevuto a una consegna applicativa.

- **LoRa:** annunci brevi soltanto con profili e primitive **già disponibili**; non introdurre nuovi preamboli, duty-cycle MAC, sleep scheduling o firmware. Se la scheda non consente controlli/rilevazioni delle finestre di ascolto, limitarsi a osservare le modalità effettivamente esposte.
- **BLE:** acquisizione locale di stato e trasferimento di log, se supportato.
- **Wi-Fi / Internet:** dataset e analisi offline o successiva, senza influire sulle finestre radio misurate.
- **USB / SD / trasporto fisico:** raccolta verificabile dei log completi.
- **DISCOVERY:** disponibilità di una campagna o evidenza; **EXACT:** manifest, hash e sequenze dei log; **SEMANTIC:** diagnosi incerta e motivata, mai affermazione di copertura senza prove.

## Test software immediato (senza hardware)

Simulare 6 nodi Python con finestre sintetiche RX/TX, clock con drift, contatti di durata variabile, perdita radio indipendente, duplicati, blackout e log mancanti. Separare *opportunità ipotizzata*, *overlap RX/TX simulato*, *pacchetto effettivamente ricevuto*, *oggetto accettato*.

Confrontare tre profili **solo simulati**: RX continuo, RX intermittente con finestre sfasate, RX intermittente con drift progressivo. Non usare il modello per attribuire automaticamente perdite alla schedulazione. Simulare esplicitamente una finestra con geometria favorevole ma nessuna sovrapposizione di ascolto, una con ascolto presente ma perdita radio e una con log incompleto.

**Criteri PASS:** le tre cause non sono confuse; ogni rapporto ha denominatore documentato; in assenza di prova indipendente la causa resta `UNKNOWN`; manifest e sequenze permettono la riproduzione del replay. Confrontare anche il costo energetico **ipotizzato** delle politiche, etichettandolo come sintetico.

## Prove hardware realmente necessarie

1. Inventariare capacità reali delle schede e dell'adapter; verificare le condizioni radio regolamentari applicabili, incluse frequenza, potenza e limiti di trasmissione.
2. In postazioni fisse controllate raccogliere log locali di TX eseguite, eventuali finestre RX realmente osservabili, timestamp con incertezza e log indipendente del ricevitore R.
3. Confrontare soltanto profili già supportati dal sistema; se non sono controllabili le finestre, misurare unicamente la **discoverability osservata**, senza pretendere una prova causale di sonno/risveglio.
4. Ripetere in più sessioni; marcare disconnessioni, riavvii e dati mancanti; estendere a checkpoint scolastici autorizzati solo dopo baseline riproducibile.

**Metriche:** opportunità controllate, TX realmente eseguite, discovery osservate, durata e incertezza delle finestre, tempo a primo contatto, consumo energetico solo se misurato e ricevute applicative distinte. Nessun PDR, autonomia, raggio o miglioramento è noto in anticipo.

## Privacy, sicurezza e rischi

ID di sessione pseudonimi temporanei; niente nominativi, GPS, percorsi o graduatorie. Dispositivi degli studenti soltanto con partecipazione volontaria, possibilità di stop locale, supervisione e niente trasmissioni durante spostamenti non autorizzati. Manifest firmati e log minimizzati con scadenza; budget airtime rigoroso e niente interferenze intenzionali.

## Anti-duplicazione e dipendenze

- **UC-008/224:** osservano o prevedono contatti; questo caso verifica specificamente **contatti persi perché non si sovrappongono le finestre di discovery**, senza inferire la causa dai soli RX.
- **UC-174:** espone finestre di servizio; qui si costruisce una verifica sperimentale delle opportunità *mancate* e della loro osservabilità.
- **UC-265:** riguarda la concorrenza di trasmettitori; qui il fenomeno cercato è la **non coincidenza RX/TX anche con un solo mittente**.
- **UC-256/178:** richiedono isolamento della campagna e denominatori verificabili.

Riferimento metodologico (non prova di prestazioni di PollicinoNet): [studio su wake-up e duty cycling LoRa, IoT 2023](https://doi.org/10.1016/j.iot.2023.100787).
