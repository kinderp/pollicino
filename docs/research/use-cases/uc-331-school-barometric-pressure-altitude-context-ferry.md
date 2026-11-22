# UC-331 — Pressione atmosferica fra costa e Peloritani: quota, tipo di dato e verifica

**Stato:** proposta documentale, 22 novembre 2026; nessun software o collaudo fisico dichiarato. **Priorità:** alta per IoT provinciale e prove LoRa. **Difficoltà:** media (validatore e simulazione), medio-alta (campagna strumentale e interpretazione).

## Problema in parole semplici
Due sensori in scuole a quote diverse restituiscono pressioni differenti. Se mescoliamo la pressione realmente misurata dal sensore (pressione di stazione) con un valore stimato come se il sensore fosse al livello del mare, un grafico può suggerire falsamente una variazione meteorologica. I dati possono arrivare attraverso relay con molte ore di ritardo. Si vuole conservare sia la misura sia la *definizione* e l'incertezza di ogni dato, non produrre previsioni del tempo.

La NOAA spiega perché le pressioni di stazione a quote diverse non sono direttamente confrontabili: https://www.noaa.gov/jetstream/atmosphere/air-pressure ; distinzione station pressure / altimeter setting: https://www.weather.gov/bou/pressure_definitions .

## Attori, nodi e scenario messinese
Docente di fisica/sistemi e reti, tre stazioni scolastiche simulate (es. costa tirrenica, Rometta, laboratorio nell'area peloritana), 3–4 schede LoRa, sensori barometrici autorizzati, PC di raccolta, revisore delle misure, studenti **volontari** come relay store-and-forward. I nomi dei luoghi identificano un progetto possibile, **non** stazioni installate o collegamenti radio provati. In campo sono preferibili punti scolastici fissi; non raccogliere tracce dei tragitti degli studenti.

## Perché PollicinoNet è adatto
Le osservazioni piccole possono rimanere nella coda del logger e passare al prossimo relay; il destinatario può ricevere il record dopo che il collegamento diretto è scomparso. I riferimenti agli strumenti, ai metodi e alle versioni possono essere ricongiunti successivamente. DISCOVERY (dato disponibile), EXACT (record/protocollo identificato) e SEMANTIC (domanda del docente) restano contratti informativi, non nuove radio.

## Bearer e carichi
- **LoRa, PHY congelato:** solo micro-record consentiti dall'adapter, identificativo del lotto, richiesta compatta, hash/receipts e piccoli riepiloghi; non inviare grafici o serie corpose.
- **BLE:** lettura diagnostica locale da logger a PC/smartphone di laboratorio, se supportata.
- **Wi-Fi/LAN/Internet:** serie complete, documentazione, grafici e verifica da PC; Internet soltanto se disponibile e autorizzato.
- **USB/SD e trasporto fisico:** record grezzi e strumenti; tenere distinta la consegna del supporto dalla consegna radio.

## Record suggerito
pressure_record_id; station_code (non casa di studente); measurement_interval; timestamp_quality; pressure_pa; pressure_kind = STATION_RAW | SEA_LEVEL_DERIVED | UNKNOWN; elevation_m; elevation_source; temperature_c_if_used; sensor_model; sensor_calibration_id; method_version; uncertainty_note; original_record_hash; revision_id; auth_signature_if_supported.

La conversione a pressione riferita al mare è un *derivato* con formula, parametri e limiti documentati, mai una correzione implicita. Se quota/temperatura/metodo non sono adeguati, riportare **NON_CONFRONTABILE**. Non sovrascrivere il dato grezzo con la stima.

## Software immediato (specificato, NON eseguito)
Generare 3 stazioni virtuali × 96 record ciascuna, con quota fittizia nota per due, terza ignota; introdurre 8 record senza tipo di pressione, 6 duplicati, 12 arrivi tardivi, 4 unità errate (Pa/hPa) e 4 reset d'orologio. Confrontare un grafico ingenuo di tutte le pressioni con il validatore che mostra pressione di stazione distinta dalla derivata a livello del mare. Verificare: nessun dato senza quota/metodo è convertito automaticamente; i duplicati non raddoppiano le medie; ritardi non riscrivono timestamp originari; il report mantiene UNKNOWN e il denominatore delle misure attese. Usare Python/CSV, niente hardware e nessuna stima di copertura.

## Hardware fisico richiesto (NON eseguito)
Prima **due sensori barometrici e un riferimento appropriato** nello stesso laboratorio a quota uguale, per verificare offset e stabilità; 3–4 schede LoRa e 2 PC per consegna A→B→C con contatti volutamente separati. Solo in una fase successiva ripetere a due postazioni autorizzate a quote differenti, documentando quota/sorgente e condizioni del sensore. Log separati di tentativo, trasmissione osservabile, ricezione e accettazione applicativa; misurare soltanto con strumentazione reale PDR/tempi/energia. Nessuna promessa di copertura intercomunale, calibrazione o accuratezza.

## Privacy, sicurezza e criteri
Usare codici di stazione non personali, autorizzazioni dei laboratori, timestamp a granularità necessaria, nessun GPS di studenti, conservazione breve; autenticare i pacchetti e mantenere raw-data hash. Nessun sistema di allerta meteo o protezione civile. **PASS software** solo se i casi noti vengono marcati coerentemente; **FAIL** se si confondono le tipologie di pressione o si inventa una quota; **UNKNOWN** se mancano campioni/riferimenti. Non toccare PHY, MAC, driver o firmware.

## Anti-duplicazione
UC-003 gestisce sensori rurali generici; UC-031 è la provenienza della calibrazione; UC-123 riguarda la qualità degli orologi; UC-197 riguarda dati per condizioni meteo-incendi (senza allerta); UC-264 studia la brezza marina. **UC-331 tratta specificamente il confronto scientifico tra pressione di stazione e pressione derivata al mare con quota/metodo/qualità espliciti in una rete DTN scolastica.**