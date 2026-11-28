# UC-350 — Osservatorio scolastico del vento: medie circolari ricomponibili

**Stato:** proposta documentale, 28 novembre 2026; nessun test eseguito. Difficoltà media (software), medio-alta (misure fisiche). PHY LoRa congelato, MAC, driver e firmware invariati. Nessuna previsione o allerta meteo.

## Problema e user story
Due osservazioni di direzione da 350° e 10° danno una media aritmetica di 180°, ma la direzione media circolare è nord (0°). Anche una media di medie di finestre con numerosità diverse può essere sbagliata. Con campioni persi, duplicati e consegne tardive, l'errore diventa difficile da individuare.

Come docente voglio che un logger conservi un riepilogo piccolo ma ricomponibile di finestre di direzione, affinché un collector possa unire segmenti disgiunti e comparabili senza ricevere continuamente le letture grezze.

## Attori e scenario
Due stazioni didattiche fisse autorizzate, ad esempio presso scuole a Milazzo e Rometta, banderuole/sensori, logger, revisore e 3–5 relay degli studenti. Si confrontano periodi e siti separatamente; un riepilogo multisito richiede un protocollo e pesi espliciti, non è una misura del vento locale. I relay conservano e portano record durante contatti successivi. Nessun itinerario personale.

## PollicinoNet, contratti e bearer
- DISCOVERY: annuncio di finestre, qualità e schema disponibili.
- EXACT: ID stazione, epoca, finestra e segmento, hash dell'evidenza, unità, convenzione meteorologica FROM, riferimento nord, criterio calma, precisione e metodo. Un riepilogo non equivale alla serie grezza.
- SEMANTIC: direzione media, variabilità e qualità, non una previsione.
LoRa per riepiloghi compatti se compatibili con il budget esistente; BLE per logger; Wi-Fi/Internet/USB/trasporto fisico per serie e calibrazione.

Schema logico: {station, epoch, window, segment_id, expected_count, valid_count, calm_count, invalid_count, sum_sin, sum_cos, method_id, north_reference, convention, quality, evidence_hash}. Per la media di direzione a pesi uguali (non velocità media vettoriale), ogni angolo valido theta contribuisce sin(theta) e cos(theta); sommare le componenti dei segmenti non sovrapposti, calcolare atan2(sum_sin, sum_cos) in gradi modulo 360. La lunghezza del vettore risultante normalizzata R = hypot(sum_sin,sum_cos)/valid_count è un indicatore di concentrazione, non una misura di velocità. Escludere calma/direzione non valida secondo protocollo dichiarato; quando R è prossimo a zero rispetto a una soglia predefinita oppure n=0, direzione non interpretabile. Per precisione numerica scegliere prima tolleranze e codifica. Non unire segmenti sovrapposti, epoche o orientamenti incompatibili. La revisione tardiva sostituisce una versione solo con lineage verificabile e ricalcolo, non si somma alla precedente.

## Software immediato
12 finestre sintetiche, 2 stazioni, segmenti di numerosità disuguale; includere 350°/10°, 90°/270°, calma, assenze, duplicati, conflitti di versione, riferimento nord errato, sovrapposizioni, reboot e consegna fuori ordine. Confrontare calcolo diretto sui campioni con fusione dei riepiloghi entro tolleranza. Eseguire un baseline ingenuo in modo da mostrare l'errore della media aritmetica.
PASS: 350°/10° dà 0° entro tolleranza circolare; direzioni opposte ugualmente pesate non danno una direzione certa; i duplicati non incrementano n; campioni mancanti non sono calma; la copertura viene esposta; non si ricostruiscono distribuzioni o sequenza temporale dai soli momenti. Misurare anche byte logici e differenze dovute alla quantizzazione, senza dedurre airtime reale.

## Hardware e sicurezza
In laboratorio: banderuola/encoder manuale con goniometro di riferimento, piccoli supporti stabili, 3–5 schede e 2 PC. Validare orientamento noto, poi eventuale prova in cortile con sensori fissati in sicurezza e supervisione. Niente tetti, strade, temporali o installazioni pubbliche non autorizzate. Misurare errore rispetto al riferimento, eventuali settori ciechi, consegne e bytes reali per bearer. Nessuna accuratezza o copertura presunta.
Pseudonimi per dispositivi, siti scolastici a granularità concordata, record firmati, limiti anti-replay, nessun dato personale o tracciamento. Le letture non sono bollettini meteo ufficiali.

## Distinzione e riferimento
UC-264 studia l'inizio candidato della brezza marina, UC-331 pressione/quota, UC-345 contatori energetici, UC-346 identità delle osservazioni. Qui si studia l'aggregazione matematica di dati angolari in presenza di segmenti disgiunti e ritardati, non l'individuazione di una transizione meteorologica.
NOAA NDBC, metodi di media del vento: https://www.ndbc.noaa.gov/faq/wndav.shtml (media di versori distinta da media vettoriale pesata con velocità).
