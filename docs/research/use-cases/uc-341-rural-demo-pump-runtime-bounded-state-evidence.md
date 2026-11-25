# UC-341 — IoT rurale: durata di funzionamento di una pompa dimostrativa con eventi incompleti

**Stato: 25 novembre 2026, proposta documentale, non implementata né testata. Difficoltà media/medio-alta. PHY LoRa congelato, MAC, driver e firmware invariati.**

## Problema, attori e scenario
Un sensore registra ON/OFF di una pompa dimostrativa per irrigazione. Un evento OFF può mancare, essere duplicato o giungere molto dopo l'ON. La durata ricostruita può essere falsa anche quando tutti i messaggi ricevuti sono autentici. La domanda è: quanta parte del periodo è certamente ON, certamente OFF o sconosciuta? Non stimare litri erogati dal solo tempo di funzionamento.

Due banchi scolastici fittizi a Rometta e Spadafora, logger, contatto/pulsante o LED a bassa tensione (non una pompa reale nella prima fase), nodo LoRa, relay volontari, collector di Milazzo e docente. I relay trasportano i riepiloghi e i log anche dopo il termine dell'esperimento. Nessun collegamento diretto fra comuni è presupposto.

## Perché PollicinoNet e bearer
Il sensore produce poche transizioni, checkpoint di stato e intervalli di completezza: adatti alla consegna asincrona. Una sequenza di transizioni è differente da un campione periodico: conoscere lo stato ai due estremi di un buco non prova che sia rimasto invariato.
- LoRa: piccoli record di stato, epoca, sequenza e richieste di segmenti mancanti, nei limiti dell'adapter.
- BLE: diagnostica e segmenti locali; Wi-Fi/LAN/Internet: serie complete, log grezzi, configurazione e analisi.
- USB/SD/trasporto fisico: recupero dei log originali tramite un relay scolastico.
- DISCOVERY: segmenti disponibili; EXACT: sequenze, hash e manifest di completezza; SEMANTIC: riepilogo di durata con incertezza, mai una misura indipendente di portata o consumo.

StateEdge={station_scope, boot_epoch, seq, monotonic_time, clock_uncertainty, stable_state, debounce_profile, evidence_hash}; Coverage={epoch, from, to, coverage_claim, logger_health, source_hash}. I clock devono essere comparabili o le finestre marcate UNKNOWN. Un contatto meccanico può rimbalzare: riferimento Arduino Debounce (https://docs.arduino.cc/built-in-examples/digital/Debounce/). La durata del debounce deve essere scelta e verificata per il dispositivo effettivo; non assumere che ogni impulso sia una transizione reale.

## Software subito (piano, non eseguito)
Generare 12 sessioni sintetiche di durata nota con ground truth, LED virtuale e traccia degli ingressi. Iniettare rimbalzi, evento OFF mancante, due eventi persi con stesso stato ai bordi del buco, log duplicati, riavvio con contatore azzerato, clock incerto e ritardi. Confrontare:
- baseline che accoppia ON/OFF in ordine di arrivo (deliberatamente errata);
- ricostruzione per epoca/seq con eventi validati, completezza e intervalli conservativi.

Per una finestra allineata, sommare solo tratti ON supportati da una traccia continua affidabile e classificare il resto in OFF o UNKNOWN; durata minima ON = ON noto; massima = ON noto + UNKNOWN. Se estremi temporali incerti, allargare i limiti o sospendere il risultato. Nessuna interpolazione silenziosa; recuperare segmenti EXACT e ricalcolare con revisione. Un heartbeat senza garanzia di acquisizione continua non prova assenza di transizioni.
Gate: ground truth contenuto nell'intervallo di stima del simulatore, duplicati non cambiano risultato, somma dei tre stati copre la finestra, reset e buchi non generano falsa certezza; riportare ampiezza dell'intervallo, numero di buchi recuperati e bias della baseline come dati simulati.

## Hardware reale
3–4 schede, due PC, pulsante/contatto, LED a bassa tensione, breadboard e riferimento indipendente (secondo logger o cronometro supervisionato). Provare una sequenza ON/OFF nota, disconnessioni di applicazione, perdita di log e successivo recupero via relay. Misurare realmente tempi, rimbalzi, completezza e ritardo di recapito; la precisione del logger non è nota prima della calibrazione. Nessun intervento su pompe, rete elettrica, acquedotti o irrigazione reale; nessun comando remoto.

## Privacy/sicurezza
Solo banchi didattici, ID temporanei, nessuna abitazione o orario di presenza personale; non osservare consumi di utenti o comportamenti. Autenticare manifest, limitare retention e mantenere l'accesso ai log presso il docente. Nessuna diagnosi di guasto o garanzia operativa dell'impianto.

## Anti-duplicazione
UC-131 ripara campioni di serie temporali; UC-093 ricostruisce causalità; UC-302 riconcilia contatori cumulativi dopo reset; UC-146 coordina un budget idrico; UC-080 segue condizioni di un bene in movimento. UC-341 calcola specificamente **limiti conservativi della durata di uno stato binario a fronte di transizioni mancanti e rimbalzo**, senza inventare litri o consumi.
