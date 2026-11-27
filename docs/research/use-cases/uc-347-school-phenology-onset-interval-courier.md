# UC-347 — Fenologia scolastica: quando è iniziata la fioritura?

**Stato 2026-11-27:** proposta, nessun rilievo biologico o radio eseguito. **Difficoltà:** media. Nessuna modifica a PHY LoRa congelato, MAC, driver o firmware.

## Problema concreto
Se un gruppo vede una pianta senza fiori lunedì e con fiori venerdì, venerdì è la prima osservazione positiva, non necessariamente l'inizio reale. Se il record di mercoledì arriva in ritardo, può restringere l'intervallo. Le assenze di visite e le osservazioni incerte non sono osservazioni negative. Una seconda fioritura o fiori già scomparsi non vanno confusi con il primo episodio stagionale.

## Attori e scenario
Docenti di Scienze e Informatica, osservatori supervisionati, piante comuni in aiuole scolastiche autorizzate, cache di sede, relay volontari e revisore. Ipotesi: confrontare aiuole della costa a Spadafora/Venetico e una postazione scolastica più elevata nei Peloritani, se autorizzata; nessuna attribuzione di quota specifica o collegamento radio garantito. I relay degli studenti trasportano micro-record durante i normali spostamenti, senza itinerari personali.

## Perché PollicinoNet e contratto
Visite brevi con eventi piccoli e utili anche in differita. Manifest con codice pianta/sito pubblico non personale, specie e definizione della fenofase/versione, visit_id, tempo di osservazione e qualità, esito YES/NO/UNCERTAIN/NOT_VISITED, revisione, eventuale foto hash. Il collector ordina per tempo osservato, non di ricezione. Per una transizione documentata NO→YES, con identità/metodo coerenti, l'intervallo candidato è dopo l'ultima NO valida e fino alla prima YES valida. Senza NO precedente, il limite inferiore è ignoto; senza YES non si dichiara inizio. L'intervallo è per l'episodio osservato e non prova assenza di episodi fra visite; conflitti e cambiamenti di fenofase richiedono revisione. Versionare il risultato derivato e preservare prove originali.
- DISCOVERY: campagna e disponibilità record.
- EXACT: osservazioni/manifest e revisioni.
- SEMANTIC: intervallo candidato, ignoto o in revisione, mai una data certa inventata.

## Bearer
LoRa: stati compatti/visit_id/annunci di evidenza entro budget; BLE: scambio locale di schede; Wi-Fi/Internet: foto autorizzate, definizioni, serie complete; USB o trasporto fisico: backup dei registri. Foto e dati voluminosi non su LoRa.

## Software proposto
Sei piante virtuali, quattro settimane, calendario e transizioni sintetiche note; iniettare visite saltate, NO tardiva, duplicati, YES incerta, tempo ignoto, conflitti, seconda fioritura e revisioni. Confrontare stima ingenua (primo YES = giorno esatto; ricezione = osservazione) con intervalli e stati espliciti. Misurare ampiezza intervalli, quota senza limiti, errori di classificazione e bytes di controllo. PASS: nei casi a transizione unica e osservazioni valide l'intervallo contiene il vero inizio simulato; nessuna visita mancante diventa NO; record tardivo ricalcola in modo tracciabile; ambiguità non producono data certa. Test non eseguito.

## Hardware reale
3–5 schede, due PC, schede cartacee o app locale; fotografie opzionali, nessun sensore necessario. Prova iniziale con schede simulate in aula e poi visite periodiche alle stesse piante. Verificare protocollo e concordanza tra osservatori; conservare anche visite non valide. Un confronto costa/quota richiede campioni e metodo appropriati, non permette da solo inferenze climatiche o causali. Misurare separatamente trasporto e qualità delle osservazioni.

## Privacy/sicurezza
Niente volti, nomi, abitazioni, geotag di studenti o posizione di specie protette; minimizzare coordinate dei siti, usare esclusivamente piante comuni autorizzate e immagini proprie, limitare accessi e durata. Non raccogliere o danneggiare piante.

## Distinzione e fonti
UC-185 distingue non rilevato da non osservato; UC-267 documenta la cura degli alberi; UC-314 considera rilievi di biodiversità. Qui l'output primario è un intervallo temporale di transizione fenologica, aggiornabile con consegne tardive e non convertibile in data certa.
Riferimento: [USA National Phenology Network, Phenology Observation Portal](https://data.usanpn.org/observations/) (stato presenza/assenza per visita, stime di inizio/fine); [FAQ Nature's Notebook](https://www.usanpn.org/nn/faq) (definizioni e limiti di specifiche fenofasi). Nessuna adesione al programma presupposta.
