# UC-309 — Sensori economici di particolato: umidità e qualità del dato prima del confronto

**Stato al 13 novembre 2026:** nuova proposta documentale, nessun esperimento eseguito. **Difficoltà:** medio-alta, alta per calibrazione contro riferimento. Nessun intervento su PHY LoRa, MAC, firmware o driver.

## Problema concreto
Due postazioni scolastiche misurano il particolato con sensori ottici economici. Una si trova vicino alla costa, dove l'umidità relativa può variare molto. Il sensore riporta valori più alti, ma una parte della differenza potrebbe dipendere dall'acqua assorbita dalle particelle e dai limiti dello strumento. Senza contesto, il grafico distribuito induce conclusioni errate sulla qualità dell'aria.

**Domanda:** un aggregatore offline può evitare confronti di PM2.5 non giustificati quando mancano umidità, temperatura, controllo dello strumento o intervalli di misura completi?

## Attori, nodi e scenario provinciale
Tre postazioni fisse ipotetiche (per esempio Rometta, Venetico e un sito interno dei Peloritani, **non già installate**), sensore ottico PM, sensore temperatura/umidità, microcontrollore/logger, 4–6 schede relay LoRa, due PC cache, docente/revisore. Le scuole possono coordinare un piccolo esperimento interdisciplinare senza installare strumenti vicino a sorgenti pericolose e senza monitorare persone.

## Perché PollicinoNet
La trasmissione differita di piccoli **record di qualità** non richiede Internet continuo. La rete può trasportare sommari e richieste di recupero, mentre le misure grezze complete e i profili di calibrazione passano su bearer più capienti. La catena EXACT mantiene i dati della postazione legati al modello e alla versione della procedura. La semplice consegna corretta non rende il sensore scientificamente affidabile.

- **DISCOVERY:** ID di postazione e disponibilità di intervalli autorizzati; niente descrizioni di persone.
- **EXACT:** intervallo di campionamento, unità, modello/versione sensore, raw-vs-corrected, versione eventuale correzione, umidità/temperatura contestuali, data di misura e qualità del timestamp, flag di completezza.
- **SEMANTIC:** categoria descrittiva “monitoraggio particolato didattico”; nessuna certificazione di superamento soglie regolatorie o conseguenze sanitarie.

## Bearer
- **LoRa:** micro-record compatti, stato di qualità e richieste, solo nei limiti e con adapter già compatibili.
- **BLE:** recupero locale di piccole finestre e diagnosi del logger.
- **Wi-Fi/LAN/Internet:** serie storiche, confronto con riferimenti e report; Internet non necessario a ricevere le capsule.
- **USB/SD/trasporto fisico:** dati grezzi, diagnostica e versioni di calibrazione fra laboratori.

## Schema di valutazione
Per ogni finestra: ID postazione temporaneo; inizio/fine misura; conteggio campioni attesi/osservati; media PM grezza in unità esplicite; umidità, temperatura e rispettiva disponibilità; modello del sensore; stato del controllo; algoritmo di eventuale correzione **con provenienza**. Stati: **RAW_OBSERVED**, **HUMIDITY_CONTEXT_MISSING**, **INCOMPLETE_WINDOW**, **CONTEXT_REVIEW_REQUIRED**, **REFERENCE_VALIDATED** (solo se esiste una valida verifica esterna), **UNKNOWN**.

Una formula di correzione non va inventata dai dati sintetici. Un sensore ottico non è una stazione normativa per definizione; per valutazioni ambientali formali occorrono strumenti e protocolli adeguati.

## Prova software immediata — non eseguita
Generare **tre stazioni e 96 finestre sintetiche** di misura, con lo stesso segnale latente artificiale e disturbi fittizi legati all'umidità per una parte dei dati. Inserire mancanza dell'RH, differenze di unità, osservazioni tardive, finestre incomplete, identificativo errato di correzione, riavvii, duplicati e due sensori con modelli diversi.

Confrontare una media ingenua delle ultime letture con un aggregatore che rifiuta confronti incompatibili e separa grezzo, stima corretta e riferimento verificato.

**Criteri di accettazione futuri:**
1. Un valore grezzo non è presentato come corretto/calibrato.
2. RH mancante e finestra incompleta non diventano automaticamente zero o valori medi affidabili.
3. Stessa unità e profilo validato sono prerequisiti di un confronto quantitativo.
4. Messaggi fuori ordine non cambiano la data di acquisizione; duplicati non aumentano il denominatore.
5. Il sistema non produce allerte sanitarie/ambientali ufficiali, né stima benefici di salute da dati non validati.

## Prove fisiche richieste
Prima due sensori PM economici e sensori RH/T in **ambiente controllato e autorizzato**, 3–4 schede LoRa e due PC; stabilire controlli e cicli di misura, senza generare deliberatamente fumo o polveri. In seguito co-locare periodicamente strumenti comparabili con supervisione e, per conclusioni quantitative, confrontare con una **stazione/metodo di riferimento** e protocolli riconosciuti. La rete distribuita può testare trasferimento, perdita di osservazioni e ricevute, ma **non prova l'accuratezza del PM** senza riferimento indipendente. Nessuna copertura o autonomia presunta fra comuni.

## Privacy, sicurezza e limiti
Solo postazioni autorizzate, nessuna posizione di abitazione, nessuna telemetria personale o identificazione degli studenti. Metadati di laboratorio non necessariamente pubblici. Le misure sono **didattiche**: vietato usarle come dato certificato, indicatore clinico o allarme. Sensori e alimentatori sicuri, validare regolamenti e autorizzazioni prima di installazioni reali.

## Non duplicazione
**UC-003** trasporta generici dati da sensori, **UC-031/UC-166** documentano calibrazione e co-locazione, **UC-228** studia il bias della disponibilità dei dati, **UC-254** CO2, **UC-282** epoche di modelli edge AI. **UC-309** studia il **confondimento specifico RH/particolato ottico** e la decisione di confrontabilità di finestre differite, senza promettere correzioni universali.

## Fonti tecniche
- Di Antonio et al., *The influence of humidity on the performance of a low-cost air particle mass sensor and the effect of atmospheric fog*, Atmospheric Measurement Techniques (2018): https://amt.copernicus.org/articles/11/4883/2018/amt-11-4883-2018.html
- US EPA, *Enhanced Air Sensor Guidebook* (2022): https://www.epa.gov/air-sensor-toolbox/how-use-air-sensors-air-sensor-guidebook
