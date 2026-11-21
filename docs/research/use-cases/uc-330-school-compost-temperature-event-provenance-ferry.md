# UC-330 — Compostiere scolastiche: temperatura, posizione della sonda ed eventi di rimescolamento

**Stato (21 novembre 2026):** proposta IoT didattica, nessun sensore o cumulo utilizzato, nessuna curva di temperatura misurata. **Difficoltà:** bassa/media nel software; media/medio-alta nel collaudo strumentale e nella gestione responsabile di materiale organico. PHY LoRa, MAC, driver e firmware non modificati.

## Problema
In una compostiera la temperatura dipende anche dalla profondità della sonda e dagli eventi di gestione. Dopo un rimescolamento la sonda può essere spostata e un logger può consegnare misure fuori ordine. Se confrontiamo semplicemente l'ultimo valore ricevuto da due scuole, potremmo attribuire falsamente al processo biologico un salto causato dalla misura o dal rimescolamento.

**Obiettivo:** un diario temporale di osservazioni e interventi, con misure confrontabili e informazioni mancanti dichiarate. Nessuna pretesa di certificare compost maturo, inattivazione dei patogeni o sicurezza di utilizzo agricolo.

## Attori, luoghi e rete
Due piccoli contenitori didattici sorvegliati, sonde a bassa tensione, un logger locale per sede, docente responsabile, revisore, PC e relay studenti volontari. Esempio: confronto fra compostiera scolastica a Milazzo e una a Venetico, con checkpoint intermedi a Rometta solo se realmente autorizzati e sperimentabili. I record possono attendere in coda giorni prima dell'analisi, senza localizzare gli studenti.

## Perché PollicinoNet è adatto
Ogni finestra misura pochi byte; i registri completi, foto e procedure possono viaggiare su bearer più capaci. Lo store-and-forward conserva la versione della calibrazione e l'identità della misura, ma **non** aumenta la precisione del termometro.

**CompostObservation:** station_id_pseudonymous, probe_id, calibration_profile_hash, sensor_epoch, sequence, observed_window, clock_quality, depth_cm_if_known, position_tag, temperature_C, ambient_temperature_C_if_measured, missing_reason, quality_flags, exact_record_hash.

**CompostEvent:** event_id, station_epoch, observed_window, kind (TURN/PROBE_MOVED/PROBE_REPLACED/MATERIAL_ADDED/UNKNOWN), operator_role_authorized, method_note_hash, affected_probe_ids. Stati RAW/CONTEXT_MISSING/REVIEWED/UNKNOWN. Evitare di fondere punti prima e dopo lo spostamento della sonda senza distinzione.

## Bearer previsti
- **LoRa:** avvisi e piccoli record di temperatura, sequenza ed evento, solo nel limite dell'adapter e delle regole radio esistenti.
- **BLE:** lettura locale, diagnostica e calibrazione assistita.
- **Wi-Fi/LAN/Internet:** grafici completi, configurazioni documentate e procedure approvate.
- **USB/SD/trasporto fisico:** log grezzi, foto dimostrative prive di persone e confronto di termometri fra laboratori.

## Software subito — procedura da implementare
Generare **96 finestre sintetiche per 2 compostiere** con temperatura e ambiente noti, 2 posizioni sonda, 4 eventi di gestione, un sensore bloccato, 8 duplicati e 12 osservazioni arrivate fuori ordine. Confrontare (a) grafico ingenuo ordinato per ricezione e (b) validatore che usa osservazione, epoca, calibrazione, posizione ed eventi.

**Criteri PASS:** non trasformare intervalli mancanti in zero; una sonda spostata produce una discontinuità annotata e non una deduzione di aumento/riduzione biologica; calibrazione o profondità sconosciute portano a CONTEXT_MISSING; duplicati non cambiano le statistiche; le due compostiere si confrontano solo su finestre compatibili o con avvertenza esplicita; nessun indicatore software è dichiarato prova di igienizzazione. Metriche: falsi salti attribuiti, record con contesto completo, eventi applicati correttamente, ritardo simulato, perdita di coerenza in caso di clock incerto.

## Prova fisica
**Primo banco:** una sonda impermeabile sicura a bassa tensione, acqua tiepida o substrato *inerte* e termometro di riferimento, due PC e 3–4 schede LoRa per trasferire gli aggregati, non per controllare attuatori. Spostare intenzionalmente la sonda e testare lo stesso input su più canali, registrando tutte le ricevute.

**Seconda fase facoltativa:** solo se la scuola approva una compostiera gestita correttamente, usare materiali consentiti, igiene e supervisione docente; registrare la profondità e l'evento di rimescolamento. Non chiedere agli studenti di maneggiare materiali potenzialmente contaminati o controllare temperatura per ipotetiche soglie sanitarie. Misurare PDR, tempi e consumi solo con strumenti e denominatori reali; nessuna copertura fra comuni assunta.

## Sicurezza/privacy
No dati domestici, percorsi di studenti, foto di persone o nomi di chi cura il contenitore. Sonde e circuiti protetti da umidità, alimentazione a bassa tensione; gestione organici secondo regolamento scolastico e sicurezza. Eventi firmati o autenticati solo da ruoli autorizzati, ma non si inventa un fatto fisico in assenza di osservazione. Non offrire alert sanitari o di incendio.

## Anti-duplicazione
UC-003 è il generico sensore rurale; UC-234 osserva orti scolastici; UC-267 riguarda la cura degli alberi; UC-302 gestisce contatori dei pluviometri; UC-323 falsa lettura del livello. **Qui è specifico il rapporto fra profilo termico, posizione/profondità della sonda e interventi sul materiale, trasportati in modo asincrono.**

## Riferimenti (orientamento, non misura PollicinoNet)
- EPA, *Composting At Home*, temperatura, umidità e gestione: https://www.epa.gov/recycle/composting-home
- EPA, *Approaches to Composting*, variabili di processo: https://www.epa.gov/sustainable-management-food/approaches-composting
