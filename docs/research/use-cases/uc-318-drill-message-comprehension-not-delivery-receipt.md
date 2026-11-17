# UC-318 — Esercitazioni: capire un messaggio non equivale a riceverlo

**Stato:** proposta documentale, nessuna implementazione o sperimentazione. **Priorità:** alta per rete scolastica e comunicazioni in esercitazione. **Difficoltà:** medio-alta (software), alta (validazione umana/protezione civile). **Dominio:** comunicazioni affidabili, accessibilità, esercitazioni non operative.

## Problema e contributo
Una ricevuta radio e una ricevuta applicativa dimostrano soltanto che una capsula è partita/ricevuta/accettata. Non dimostrano che chi legge abbia capito quale informazione di esercitazione veniva comunicata. Una traduzione correttamente distribuita può comunque essere ambigua. Una versione precedente ricevuta dopo quella aggiornata può creare confusione. PollicinoNet dovrebbe permettere una **prova didattica del livello di comprensione**, separata da qualsiasi ricevuta di consegna, con risposte anonime e senza certificare la capacità di reagire in una vera emergenza.

## Scenario specifico (Messina)
Un docente prepara un messaggio fittizio marcato in modo inequivocabile `ESERCITAZIONE — NON È UN ALLARME REALE`, per gruppi simulati in 3 laboratori a Messina, Rometta e Venetico. Tre cache e nodi relay LoRa scolastici lo propagano in ritardo; alcune simulazioni consegnano una revisione successiva prima della precedente. I partecipanti possono scegliere il testo semplice, la lettura audio o una traduzione **revisionata da un umano** su connessione Wi-Fi locale; rispondono a una domanda anonima su quale sia il messaggio, oppure dichiarano di non averlo compreso. Non associare risposte a persone, classi piccole o itinerari. Qualsiasi eventuale attività reale è concordata prima con dirigenti e referenti competenti e si tiene soltanto in contesti didattici controllati. Non trasmettere veri allarmi.

## Attori e nodi / bearer
- Docente autorizzato alla simulazione, revisore della comunicazione e traduzioni, 3 nodi di cache/visualizzazione, relay volontari studenti, revisore anonimo degli esiti.
- **LoRa:** solo microcapsule autorizzate, `drill_id`, versione, hash del testo firmato, stato supersession/cancel e riferimento al contenuto ricco, quando tecnicamente supportati.
- **BLE:** discovery locale facoltativa e manifesto compatto; non prova di lettura.
- **Wi-Fi/LAN/Internet:** testo semplice, accessibilità e versioni audio; dati di esercitazione; Internet non richiesto.
- **USB/trasporto fisico e carta:** fallback autorizzato per pacchetti di prova e questionari sintetici; qualunque trasferimento richiede controllo esatto e log consentiti.
- DISCOVERY, EXACT, SEMANTIC non sono bearer; evitare trasferimenti ingombranti su LoRa.

## Modello dati e distinzione delle evidenze
`drill_id`, `is_drill=true`, `issuer_signature`, `message_version`, `supersedes_version`, `expiry`, `language`, `accessibility_variant`, `human_review_status`, `content_hash`, `tx_observed`, `rx_observed`, `app_accept_receipt`, `comprehension_response`, `question_version`, `response_aggregation_window`, `withdrawal_state`, `unknown_reason`.
Gli stati del messaggio: DRAFT, APPROVED_DRILL, SUPERSEDED, CANCELLED, EXPIRED. Gli stati del questionario: NOT_ANSWERED, CORRECT_SYNTHETIC, INCORRECT_SYNTHETIC, UNKNOWN_SYNTHETIC (nessuna interpretazione sanitaria o capacità personale). Non inferire comprensione da click, apertura o consegna; evitare qualsiasi uso del risultato per voti o giudizi individuali. Aggregare soltanto in gruppi abbastanza grandi da evitare reidentificazione e non pubblicare piccoli gruppi.

## Prova software immediata — progettata, NON eseguita
Generare 3 messaggi fittizi con versione originale, correzione e cancellazione; 3 varianti testuali simulate e 36 risposte **interamente artificiali**. Tre cache ricevono in ordini diversi manifest, annullamenti e ricevute. Confrontare una baseline che conta solo `app_accept_receipt` con una pipeline che presenta percentuali di risposte artificiali per versione e categoria, mostrando sempre denominatore e dati mancanti. Non confondere una risposta assente con una errata. Per prove umane future richiedere autorizzazioni e informativa, ma oggi utilizzare solo dati sintetici.

**Criteri di accettazione:**
1. Una ricevuta radio/app non aumenta automaticamente il contatore di risposte corrette o di comprensione.
2. Una versione annullata o superata non torna corrente solo perché arriva in ritardo.
3. Il sistema presenta `N/A` o `UNKNOWN` quando mancano denominatori o versioni della domanda, mai percentuali inventate.
4. Nessun testo o quiz esce come allerta reale: identificazione visiva e crittografica dell'esercitazione.
5. Varianti non revisionate vengono trattenute; le opzioni accessibili non devono richiedere Internet esterno.
6. Nessun identificativo individuale viene memorizzato e nessuna risposta è usata per valutazioni degli studenti.

## Prove hardware necessarie — non eseguite
Iniziare con **4–6 schede LoRa**, due PC e tre checkpoint/caches logiche nella medesima scuola. Misurare separatamente osservazione TX, RX, ricevuta applicativa e disponibilità del contenuto accessibile. Le risposte di comprensione restano sintetiche per questa fase. Un'eventuale attività successiva tra scuole è subordinata a autorizzazioni, governance dei messaggi e protocollo etico; nessuna rete reale di emergenza deve dipendere da PollicinoNet e non si presuppone copertura fra Messina e gli altri comuni. Nodi trasportati volontariamente durante spostamenti ordinari, mai tracking degli studenti.

## Privacy, sicurezza, governance
Issuer e revisioni firmati; autorizzazioni del docente e della scuola; canale e interfaccia ben separati dai messaggi reali; protezione contro replay/versioni vecchie; retention breve; minimizzazione di lingue o esigenze individuali (mai usarle come profilo personale). Materiali in plain language e revisionati, non affidare alle AI la versione definitiva di istruzioni. Nessun invio verso canali di allerta pubblici o terzi senza accordi formali.

## Anti-duplicazione
- **UC-002/106/132:** messaggi firmati, traduzioni e supersession di allerte; qui si misura *se il contenuto di esercitazione è stato compreso* con indicatori separati dalla consegna.
- **UC-200:** gestione di un'esercitazione e after-action; qui introduce **questionario anonimo, denominatori, varianti, N/A e confronto comprensione-vs-delivery**.
- **UC-221:** app acceptance receipt, prova che l'app ha ricevuto, non comprensione umana.
- **UC-238/288:** accessibilità/TTS e traduzioni di contenuti, non misure didattiche di comprensione delle comunicazioni simulate.
- **UC-222:** display di stato scaduto, non gestione di comprensione con risposta umana e incertezza.

## Fonti metodologiche
- CDC, Crisis & Emergency Risk Communication (CERC): https://www.cdc.gov/cerc/php/cerc-manual/index.html
- CDC, Clear Communication Index: https://www.cdc.gov/ccindex/widget.html/1000
- CDC (2026), applicare principi di comunicazione del rischio: https://www.cdc.gov/public-health-risk-communication/php/about/understanding-and-applying-risk-communication-principles.html

**Confini:** scenari inventati e marcati esercitazione, niente allerte operative, nessuna misura radio, nessun risultato di test comprensione reali, nessuna modifica a PHY/MAC/driver/firmware.
