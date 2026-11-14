# UC-311 — Pioggia e ristagni: osservazioni scolastiche offline, non allerte idrauliche

**Stato al 14 novembre 2026:** proposta documentale. Nessuna osservazione reale, sopralluogo o test effettuato. **Difficoltà:** medio-alta; alta per qualunque uso operativo, **fuori ambito**. Nessuna modifica al PHY LoRa congelato, MAC, driver o firmware.

## Problema concreto
Dopo piogge intense, un punto vicino a una scuola può mostrare un ristagno o un tombino apparentemente ostruito. Le segnalazioni arrivano a laboratori differenti con ritardo: una foto potrebbe essere vecchia, mostrare un'ombra o provenire da un punto diverso. Un mancato sopralluogo non è una prova di assenza d'acqua. Un'osservazione didattica non deve diventare un avviso ufficiale di allagamento o una diagnosi tecnica dell'impianto di drenaggio.

**Domanda:** possiamo ricostruire un diario di osservazioni limitate, con data reale, sforzo di osservazione, revisioni e confidenze esplicite, anche con collegamenti intermittenti?

## Scenario, attori e nodi
Docenti, gruppi scolastici, eventuale responsabile autorizzato della struttura, 2-3 postazioni fisse **sicure** e autorizzate, due cache/PC e 4-6 schede relay. Esempio ipotetico: postazioni scolastiche nell'area di Rometta e Saponara, poi confronto dei protocolli fra scuole della provincia; nessuna collocazione precisa o copertura radio è dichiarata. Niente raccolta durante temporali o vicino a corsi d'acqua, tombini aperti, strade allagate o zone interdette.

## Perché PollicinoNet
Non serve Internet continuo per trasportare piccoli record di osservazione fra scuole: annunci e revisioni possono arrivare via store-and-forward. Le fotografie e i dettagli, troppo grandi per LoRa, rimangono su cache locali fino a un incontro su bearer ricco. La domanda applicativa è **quando un rilievo può essere confrontato**, non diffondere avvisi di sicurezza.

- **DISCOVERY:** identificatore pubblico/grossolano di postazione, categoria del record, epoca e disponibilità.
- **EXACT:** hash del record approvato, protocollo versione, data acquisizione separata da data consegna, osservatore con ID scolastico non pubblico e versione della revisione.
- **SEMANTIC:** etichetta di ristagno/ostruzione apparente come **ipotesi**, mai certezza causale o forecast.

## Bearer
- **LoRa:** micro-annunci di nuovi record e aggiornamenti brevi, soltanto se già supportati.
- **BLE:** raccolta da logger o device scolastico vicino a postazione.
- **Wi-Fi/Internet/LAN:** foto di prova, tavole comparative e report.
- **USB/SSD/trasporto fisico:** album/archivi da laboratori scolastici con accesso approvato.

## Dati e stati minimi
`DrainageObservation`: ID postazione consentita; ID osservazione fittizio/opaco; versione protocollo; istante/osservabilità del rilievo; `observed_at` e `received_at` distinti; condizione meteo riportata come osservata o proveniente da fonte verificabile; stato `DRY_CONFIRMED`, `POOLING_OBSERVED`, `NO_VISIT`, `PARTIAL_VIEW`, `NEEDS_REVIEW`, `STALE`; note sullo sforzo e sul punto di osservazione; hash di eventuale foto oscurata; stato autorizzazione/revisione. `DRY_CONFIRMED` richiede un sopralluogo completo e sicuro, mai la semplice assenza di dati.

## Software immediato — non eseguito
Creare 3 postazioni virtuali e **24 record sintetici**: tre `NO_VISIT`, tre `PARTIAL_VIEW`, foto/descrizioni discordanti, timestamp invertiti, record vecchi consegnati per ultimi, revisione che corregge una classificazione, una foto fittizia con volto simulato marcata **PRIVACY_BLOCKED**. Confrontare aggregazione ingenua (ultimo messaggio arrivato) con logica per tempo dell'evento, validità del protocollo e conflitti espliciti. Non simulare previsioni di piena.

**Criteri di accettazione:**
1. `NO_VISIT` e `PARTIAL_VIEW` non diventano automaticamente `DRY_CONFIRMED`.
2. Una consegna tardiva non sostituisce il rilievo successivo soltanto perché è arrivata dopo; conservare conflitti e intervalli ignoti.
3. Nessuna foto priva di revisione/privacy è distribuita; nessun nome, volto, targa, casa o percorso di studente nei report.
4. Gli stati pubblicati sono osservazioni **didattiche non operative**, mai allerta, ordine di intervento o attestazione di sicurezza.
5. LoRa trasporta solo messaggi compatibili con l'adapter, secondo policy e budget radio.

## Hardware e prove necessarie
In laboratorio, quattro schede, due PC e immagini/record artificiali per verificare gli scambi EXACT, conflitti e ritardi. Eventuale esercizio successivo: postazioni statiche sicure, **solo con condizioni meteorologiche favorevoli**, osservazione visiva autorizzata da area non esposta. Misurare consegne applicative, ritardi, tasso di record completi, dati effettivamente verificabili; **non** inferire capacità idraulica, rischio attuale, stato delle infrastrutture o tempi di risposta di enti pubblici.

## Privacy, sicurezza e limiti
Il sistema non si collega a procedure di protezione civile né le sostituisce. Per informazioni di emergenza usare esclusivamente autorità e canali ufficiali. Non si accede a tombini, sottopassi, aree allagate o tratti di torrenti. Tutti i dati di prova sono fittizi; eventuali dati reali sono minimizzati, revisionati e soggetti a retention definita. Nessuna geolocalizzazione personale continua.

## Anti-duplicazione
- **UC-049:** mappa della praticabilità dei percorsi; **qui** qualità e comparabilità di **osservazioni fisse di ristagno/drenaggio**, senza guidance stradale.
- **UC-144:** eventi da variazioni di livello nei bacini; qui **nessun allarme sensoriale** né modello idraulico.
- **UC-302:** riavvii e contatori di pluviometro; qui registrazioni visive osservate dopo l'evento.
- **UC-116/UC-185/UC-308:** regole generali per rilievi/evidenze e foto costiere; qui vocabolario di **osservazioni pluviali urbane**, completezza e vincolo di non allerta.

## Fonte metodologica
- FloodCitiSense (programma 2017–2020): osservazioni cittadine su pioggia/allagamenti abbinate a immagini, da cui trarre spunti per un esperimento **non operativo**: https://iiasa.ac.at/models-tools-data/floodcitisense
