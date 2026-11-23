# UC-335 — Infiltrazione del suolo scolastico: misure comparabili trasportate in differita

**Stato:** proposta documentale del 23 novembre 2026. Nessun dataset, test o rilievo eseguito. **Priorità:** alta come laboratorio IoT/LoRa interdisciplinare. **Difficoltà:** media software, medio-alta per misure di campo comparabili.

## Problema in parole semplici
Due gruppi misurano la velocità con cui l'acqua penetra nel terreno e trovano tempi diversi. Il suolo poteva però essere più umido all'inizio, il volume versato diverso, o il metodo non equivalente. I record arrivano in giorni diversi attraverso relay: una media senza metodo, unità e tempo di osservazione diventa ingannevole. **PollicinoNet deve custodire la misura con il suo contesto**, non prevedere frane, alluvioni o sicurezza del territorio.

## Attori e scenario provinciale
Tre laboratori scolastici fittizi fra Milazzo, Venetico e Rometta, docenti di scienze/informatica, 3–4 schede LoRa e studenti volontari come relay, PC di laboratorio, revisore. Iniziare con terriccio autorizzato e vassoi didattici. Ogni eventuale prova in giardino richiede autorizzazione: nessuno scavo in area pubblica, rilievo su pendii o scarico incontrollato d'acqua. I luoghi non rappresentano link radio misurati.

## Perché PollicinoNet e bearer
I brevi record di prova e la versione del metodo possono essere inoltrati e ricevuti in differita; fotografie, protocolli e raw log arrivano dopo e il risultato rimane collegato all'originale. **LoRa con PHY congelato:** ID, hash, richiesta, qualità o micro-record se compatibili con adapter. **BLE:** lettura da logger locale se disponibile. **Wi-Fi/LAN/Internet:** tabelle, immagini, aggregazioni, versioni dei metodi. **USB, carta e trasporto fisico:** schede e campioni leciti; questi bearer devono restare distinti nei log.

## Record suggerito
sample_id; site_code_nonpersonal; trial_id; protocol_hash; method_class=TRAY_DEMO|RING_FIELD|OTHER|UNKNOWN; area_if_applicable; input_water_volume_ml; initial_soil_moisture_method_and_quality; measurement_duration_s; uncertainty_note; observation_time_quality; receive_time; units; infiltration_observed; review_status; missing_reason; raw_sheet_hash; revision_id. Una prova in vaschetta deve mantenere DEMO_NOT_FIELD_COMPARABLE: non convertirla automaticamente in una misura di infiltrazione da anello validata.

## Software subito — proposta non eseguita
Generare 3 gruppi × 12 prove fittizie: 4 con umidità iniziale ignota, 5 con metodo TRAY_DEMO, 3 senza durata, 6 duplicati, 8 arrivi tardivi e volumi differenti. Validatore Python: (1) separa metodo, volume e unità; (2) segnala non comparabili e non li aggrega; (3) conserva UNKNOWN dove mancano dati; (4) deduplica per ID/versione mantenendo raw e provenienza; (5) ordina l'analisi per tempo di osservazione, non per arrivo. Questi numeri sono **taglie sintetiche di progetto**, non risultati di prove.

## Hardware da usare — non eseguito
Primo banco: vassoi impermeabili e vasca di raccolta, terriccio autorizzato, cilindro graduato, cronometro, eventuale bilancia, 3–4 schede LoRa e 2 PC. Repliche supervisionate senza automazione delle irrigazioni. Consegnare piccoli record A→B→C in finestre separate come UC-321; misurare ricezione e ricevuta dell'app, non presumere copertura intercomunale. **Non definire la prova con vaschetta una misura di campo.** Per un rilievo successivo seguire un protocollo riconosciuto per anello, stato iniziale, volume e repliche, con controllo di sicurezza e autorizzazione.

## Privacy, sicurezza e criteri
Niente campioni contaminati, superfici bagnate presso prese elettriche o luoghi pericolosi, niente nomi o percorsi di studenti. Hash, ruoli e retention ridotta. **PASS software** quando nessuna prova sintetica non confrontabile viene promossa a misura valida di campo; **FAIL** se demo e anello entrano nella stessa media; **UNKNOWN** se mancano metodo o qualità. Non dichiarare rischi geologici, qualità del suolo ufficiale, precisione o dati fisici; PHY, MAC, driver, firmware invariati.

## Anti-duplicazione
UC-003 raccoglie sensori rurali generici; UC-031 tiene la calibrazione; UC-144 riguarda cambi di livello in bacini; UC-146 domanda irrigua; UC-187 protocolli riproducibili fra scuole; UC-269 EC del suolo e UC-302 pluviometri. **UC-335 rende esplicita la comparabilità di prove di infiltrazione in funzione di metodo, volume, stato idrico iniziale e arrivo differito.**

## Fonti metodologiche
USDA–NRCS, Soil Health – Infiltration, metodo e ripetizioni: https://www.nrcs.usda.gov/sites/default/files/2022-10/Soil%20Infiltration.pdf

USGS, A field method for measurement of infiltration: https://pubs.usgs.gov/publication/wsp1544F
