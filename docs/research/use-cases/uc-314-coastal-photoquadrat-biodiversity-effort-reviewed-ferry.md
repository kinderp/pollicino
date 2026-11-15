# UC-314 — Biodiversità costiera con foto-quadrat e revisione distribuita

**Stato:** proposta, non attuata. **Difficoltà:** medio-alta. **Dominio:** IoT/citizen science, prove visive, edge AI facoltativa.

## Problema
Scuole diverse fotografano piccole aree costiere e cercano di confrontare presenza/copertura visibile di organismi o alghe. Immagini di dimensioni, posizione, qualità e sforzo diversi non possono essere sommate come se fossero un censimento omogeneo. Una foto può contenere organismi non identificabili, e un classificatore AI potrebbe confondere i taxa. Occorre distinguere **raccolta, revisione, confronto e conoscenza validata**, anche quando le evidenze arrivano offline.

## Scenario provinciale e attori
Laboratori a Milazzo, Rometta e Venetico analizzano fotografie **didattiche o autorizzate** di quadrati campione su eventuali tratti rocciosi idonei. Un docente identifica prima un sito accessibile e il protocollo appropriato; nessun obbligo di entrare in mare, raggiungere scogli scivolosi o raccogliere organismi. È possibile partire esclusivamente da foto sintetiche o immagini liberamente riutilizzabili. Le schede LoRa dei partecipanti e checkpoint fanno relay store-and-forward dei **metadati compatti**; i file fotografici si spostano con altri bearer.

## Attori / nodi e bearer
- Osservatori autorizzati, docente responsabile del protocollo, nodo di raccolta, 3 cache scolastiche, revisori della classificazione, eventuale edge AI.
- **LoRa:** ID campagna, versione del protocollo, hash immagine, stato revisione e richieste di immagini, entro capacità realmente supportate.
- **BLE:** manifest e piccoli metadati; **Wi-Fi/Internet:** foto integrali e batch; **SD/USB/trasporto fisico:** dataset capienti e verificati.
- La prova esatta del file richiede hash, dimensioni, licenza e ricevuta applicativa; discovery non significa che il file sia consegnato.

## Schema dati minimo
`survey_id`, `protocol_hash`, `site_public_coarse`, `quadrat_area`, `camera_height`, `sampling_date`, `surface_type`, `photo_hash`, `method`, `effort_status` (NOT_VISITED / PARTIAL / VALID), `visibility_quality`, `annotation_version`, `reviewer_status` (UNREVIEWED / REVIEWED / CONFLICTING), `taxon_claims` (sempre con incertezza). Non esporre coordinate private, fotografie con volti o metadati EXIF non necessari.

Il manuale MBON Pole-to-Pole presenta un esempio di foto-quadrat standardizzato e non estrattivo su coste rocciose. Il suo metodo **non è automaticamente valido** per tutte le spiagge messinesi o per l'identificazione di specie locali: https://marinebon.org/tools/sampling-protocol-for-monitoring-marine-biodiversity-on-rocky-shores/

## Software immediato — non eseguito
Simulare 3 siti e 24 campioni con foto artificiali o semplici hash: 6 validi, 6 parziali, 6 non eseguiti e 6 con annotatori in disaccordo; introdurre arrivi fuori ordine, duplicati, immagini senza autorizzazione, cambi di `protocol_hash` e classificatore AI non revisionato. Un collector deve ricostruire lo stato senza distruggere versioni, mantenere conflitti e consentire un confronto solo di sottoinsiemi equivalenti.

**Criteri di accettazione:** 
1. NOT_VISITED e PARTIAL non vengono conteggiati come quadrat validi con copertura zero;
2. protocolli o aree incompatibili non vengono aggregati senza esplicita normalizzazione e revisione;
3. gli output AI rimangono `CANDIDATE` fino all'approvazione del docente/esperto;
4. nessuna foto priva di diritti o manifest verificabile viene pubblicata;
5. una foto è "disponibile" soltanto dopo verifica EXACT, non dopo l'annuncio su LoRa.

## Hardware / campo — non eseguito
4 schede, due PC, fotocamera scolastica e quadro rigido **soltanto** in una postazione di facile accesso e autorizzata. Una fase avanzata, opzionale, usa una postazione costiera verificata sicura da responsabili competenti. Prima prove con immagini fittizie; non è necessaria escursione per il test di rete. Misurare separatamente accettazione dei messaggi compatti, trasporto file su bearer ricco, tempo di revisione e completezza del campionamento.

## Privacy, etica, difficoltà
Consensi per le persone eventualmente presenti, oscurare volti/targhe, rimuovere GPS EXIF, diritti e licenze sulle immagini, niente campionamento estrattivo o ingresso in zone protette senza autorizzazione. Nessuna certificazione ambientale né trend di biodiversità dai dati dimostrativi. **Difficoltà: medio-alta**, per la metodologia scientifica prima ancora che per la rete.

## Anti-duplicazione
- **UC-285:** litter/rifiuti e sforzo di sopralluogo, non foto-quadrat di copertura biologica con classificazione.
- **UC-308:** geometria confrontabile di immagini della costa/erosione, non stima della presenza/copertura biologica in quadrat.
- **UC-060/150/273:** generici trasporto visuale, mosaico e bioacustica; qui unità di campionamento, revisione biologica e protocollo comparabile.
- **UC-171:** qualità dell'acqua, non biodiversità visuale bentonica.

**Confini:** nessuna raccolta reale, nessuna specie certificata, nessuna misura radio fisica e nessuna modifica PHY LoRa.
