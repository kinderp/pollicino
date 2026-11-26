# UC-345 — IoT: consumi energetici di banchi didattici anche con campioni mancanti

**Stato (26 novembre 2026):** proposta documentale, non implementata/testata. Difficoltà media. PHY LoRa congelato, MAC, firmware e driver invariati.

## Problema e attori
Una scuola misura il consumo di LED, piccole ventole o carichi USB di prova. I campioni di potenza possono mancare durante una disconnessione, ma un contatore locale di energia potrebbe aver continuato a funzionare. Una lettura di 2 W è potenza, non energia; interpolare attraverso un buco può inventare un profilo di consumo. Docenti, logger, misuratore DC indipendente, checkpoint, relay e collector.
Scenario didattico ipotetico: banchi a Milazzo e Rometta, report a Venetico; studenti volontari trasportano riepiloghi senza tracciare spostamenti. Nessuna copertura intercomunale assunta.

## Perché PollicinoNet e bearer
Piccoli cumulati di energia e finestre di completezza possono viaggiare in ritardo; i dati ad alta frequenza restano localmente disponibili. DISCOVERY: segmenti e report disponibili; EXACT: unità, epoca, sequenza, intervallo, misura e provenienza; SEMANTIC: etichette consumo noto/stimato/sconosciuto, mai evidenza sostitutiva.
- LoRa: cumulati e stati compatti, se compatibili con adapter; BLE: diagnostica e recupero vicino; Wi-Fi/Internet: serie di potenza e confronto; USB/trasporto fisico: log e report di riferimento. Non serve inviare campioni continui su LoRa.

## Contratto e criterio
EnergyCounter={meter_scope, epoch, seq, monotonic_time, clock_quality, cumulative_Wh, unit, continuity_evidence, calibration_id}; PowerSample={meter_scope, epoch, interval, watts, sampling_method, quality}; Report={interval, counter_delta_Wh?, estimated_Wh?, bounds?, coverage, source_hashes, state}.
L'energia in Wh è integrale della potenza W rispetto al tempo in ore. Un delta tra due letture dello stesso contatore è utilizzabile solo con continuità, assenza di reset non risolti e incertezza dichiarata. Non ricostruisce la forma della curva né la ripartizione fra sottointervalli. Per stima da campioni separare copertura e assunzioni; per buchi si può usare [0,Pmax*durata] soltanto se il carico è non rigenerativo e il limite Pmax è giustificato. Altrimenti UNKNOWN. Mai sommare delta e integrazione come energie indipendenti dello stesso periodo. Riferimento: https://docs.openenergymonitor.org/emoncms/daily-kwh.html distingue ingressi in W e cumulati Wh/kWh; non adottare interpolazione grafica come evidenza.

## Software subito (piano)
12 sessioni sintetiche con profilo di riferimento noto: carico costante, impulsi fra campioni, contatore continuo con pacchetti persi, reset, overflow non risolto, duplicati, clock incerto, unità Wh/kWh, mismatch fra misuratori e log arrivati tardi. Esempio matematico: cumulati validi 10 e 13 Wh alle estremità implicano 3 Wh sull'intero intervallo, non 1,5 Wh in ciascuna metà.
Gate: delta valido recuperato anche con campioni persi, nessuna energia inventata quando mancano continuità o limiti, intervallo conservativo contiene ground truth sintetico quando le premesse valgono, nessun doppio conteggio. Misurare errore di stima, ampiezza intervalli, completezza e ritardo del recupero; distinguere stima da misura.

## Hardware, sicurezza e privacy
3–4 schede LoRa, 2 PC, carico USB commerciale a bassissima tensione, misuratore USB/DC con log e un riferimento indipendente idoneo. Prova supervisionata con profili ripetibili e spegnimento controllato del trasferimento, non del misuratore, poi test separato di reset. Verificare risoluzione, calibrazione, sincronizzazione e consumi dei logger; niente rete elettrica, quadri, impianti domestici, batterie aperte o controllo remoto. Solo banchi didattici e pseudonimi; nessuna inferenza di occupazione delle case o abitudini degli studenti. Misure fisiche e accuratezza ancora da ottenere.

## Distinzione
UC-052 coordina carichi, UC-252 misura autonomia del relay, UC-292 verifica fattibilità solare, UC-302 tratta contatori di pioggia, UC-341 durata di stato ON/OFF. UC-345 confronta due rappresentazioni della stessa energia (contatore cumulativo e integrazione di potenza campionata) e conserva il totale senza inventare la distribuzione temporale.
