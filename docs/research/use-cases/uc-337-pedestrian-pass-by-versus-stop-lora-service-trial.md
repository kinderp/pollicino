# UC-337 — Passare davanti al checkpoint oppure fermarsi? Prova LoRa con relay in movimento

**Stato (24 novembre 2026):** proposta sperimentale non implementata; nessun test software o radio eseguito. Difficoltà software media, fisica medio-alta. PHY LoRa congelato, MAC, driver e firmware invariati.

## Problema e attori
Una scheda trasportata dagli studenti può incontrare un checkpoint durante un normale passaggio senza che il contatto duri abbastanza da completare una consegna. Come responsabile del testbed voglio decidere se il semplice passaggio sia sufficiente o se convenga un breve stop volontario presso la postazione. Attori: docente, checkpoint fisso, relay mobile, destinatario applicativo, ricevitore/testimone e PC collector.

Scenario iniziale: un cortile autorizzato a Milazzo o Venetico, con carrello manuale a bassa velocità o adulto volontario; due estremi e un punto di sosta segnati, senza GPS, studenti identificati o traffico stradale. Replica indipendente a Rometta; non implica collegamento radio intercomunale. In seguito i relay volontari possono trasportare capsule fra isole usando spostamenti già previsti, senza deviazioni imposte.

## Perché PollicinoNet e bearer
Una coda persistente permette di completare ciò che è possibile e conservare il resto per un incontro successivo. DISCOVERY indica un contatto, non una consegna; EXACT lega la ricevuta all'oggetto e all'applicazione; SEMANTIC presenta il risultato solo se sostenuto dalle prove.
- LoRa: capsule piccole e ricevute compatibili con adapter e budget correnti, senza cambiare il profilo.
- BLE: braccio separato per sincronizzazione vicina, se supportato.
- Wi-Fi/Internet: esportazione log e trasferimenti più grandi in bracci distinti; nessun percorso alternativo durante il test LoRa.
- Trasporto fisico: coda nel relay tra checkpoint o recupero dei log tramite USB, non conteggiato come trasmissione radio.

## Contratto e software immediato
Proposta `PassTrial={trial_id,block_id,condition,board_profile,object_ids,predeclared_zone_window,clock_quality,tx_evidence,rx_evidence,app_accept_ids,pending_ids,missing_logs,bearer}`. Le finestre sperimentali di passaggio sono definite indipendentemente dai pacchetti, non ricavate dal primo/ultimo RSSI. Nessuna telemetria individuale.
Simulare 3 condizioni (fermo per tutta la finestra, passaggio senza stop, passaggio con breve stop), 12 blocchi per condizione e 3 capsule nominali per blocco, con tempi di servizio artificiali, contatti interrotti, receipt tardive, reboot, duplicati e log mancanti. Confrontare accettazione entro la finestra e dopo incontri successivi; riportare anche le capsule non tentate per budget e distinguere ricezione radio, custodia e accettazione. Test di riferimento: una capsula arrivata dopo il termine non può contare come successo del passaggio, una duplicata conta una volta, un log mancante rende l'attribuzione inconcludente. Nessun numero simulato è una misura di capacità radio.

## Hardware e criteri di accettazione
4 schede (mobile, checkpoint, testimone e riserva), 2 PC, carrello/manuale o adulto consenziente, cronometro e marcatori del percorso sperimentale. Blocchi appaiati e ordine controbilanciato; stesso dispositivo, orientamento, altezza, alimentazione, payload e tratto. Il braccio fermo è controllo di servizio, non prova che le geometrie siano equivalenti. La sosta ha durata fissata prima del test; non cambiare ritmo di trasmissione per compensare perdite. Verificare che i tentativi rientrino nei vincoli radio applicabili; interrompere localmente quando necessario. Registrare TX, RX, ricevute e tempi con incertezza; se non si può escludere un bearer alternativo o mancano log, esito INCONCLUSIVE. Misure proposte: accettazioni uniche entro finestra per oggetti previsti e per trasmissioni osservate (denominatori distinti), attesa, coda residua, airtime solo se misurabile, intervalli d'incertezza. Nessuna conclusione di copertura, velocità ottimale o PDR prima della prova.

## Privacy, sicurezza, originalità
Solo payload e ID di test effimeri; niente GPS, nomi, orari di ingresso/uscita o traiettorie reali; cancellare i log fini dopo revisione secondo policy. Niente partecipazione obbligatoria. UC-310 confronta zaino/corpo con volontario fermo; UC-280 riguarda veicolo parcheggiato; UC-304 simula concorrenza di più relay statici; UC-188 studia fattibilità generica del payload. Qui la variabile è la scelta operativa **passaggio fisico singolo vs sosta breve**, con coda residua e controllo fermo. UC-321 resta il successivo test su due finestre disgiunte.

Riferimento concettuale: RFC 9171, sez. 5.8, https://datatracker.ietf.org/doc/html/rfc9171#section-5.8 (contatti intermittenti e trasferimenti incompleti; nessuna dichiarazione di compatibilità BPv7 o prestazione PollicinoNet).
