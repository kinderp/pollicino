# UC-231 — Registro del budget radio locale e qualità dell'evidenza di trasmissione

**Stato:** proposta documentale del 20 ottobre 2026; nessun risultato RF acquisito.

## Problema
Una pianificazione degli esperimenti non dice quanto ogni scheda abbia effettivamente trasmesso. Un nodo che ritenta più volte può consumare risorse senza accorgersene. Serve un registro applicativo prudente che distingua **trasmissioni richieste**, **trasmissioni dichiarate dal sistema** e **trasmissioni osservate da strumenti indipendenti**: non sono prove intercambiabili.

## Attori, rete e scenario Messina
Docente e tecnico coordinatori, 6–10 schede LoRa in due checkpoint scolastici autorizzati a Messina e nell'area Villafranca–Rometta, uno o più ricevitori di confronto. Gli studenti partecipano solo a sessioni supervisionate e senza monitoraggio dei tragitti.

## Perché PollicinoNet; bearer
LoRa porta solo riepiloghi piccoli e identificativi di sessione. BLE/Wi-Fi e Internet autorizzato trasferiscono registri più grandi; USB/SD funge da trasporto fisico. Store-and-forward consente di raccogliere i registri in seguito. **Non si modifica il PHY LoRa congelato.**

## Test software immediato
Simulare 10 nodi con budget di prova, messaggi di dimensioni differenti, retry, riavvii e log mancanti. Un guard applicativo restituisce `ALLOW`, `DEFER` o `UNKNOWN`. Verificare che l'assenza di log non venga interpretata come assenza di trasmissione. Confrontare budget pianificato, conteggi attribuiti e verità sintetica nota; registrare anche i casi non classificabili.

## Prova fisica necessaria
Usare 6–10 schede e osservazioni indipendenti, registrando configurazione, dimensioni, modalità di misura e trasmissioni effettivamente osservabili. Prima delle trasmissioni verificare frequenza, potenza, antenna e vincoli applicabili alla sottobanda. Un contatore applicativo **non certifica la conformità normativa** né fornisce valori misurati di airtime.

## Privacy, sicurezza, difficoltà e successo
Usare identificativi temporanei di prova, log a durata limitata, nessuna graduatoria personale, stop locale e limiti prudenti. Difficoltà **medio-alta**. Successo: motivazione verificabile di ogni defer e distinzione esplicita `misurato/stimato/sconosciuto`.

## Originalità
UC-063 osserva lo spettro, UC-097 la campagna, UC-226 coordina la contemporaneità delle campagne. **UC-231 introduce un rendiconto e un guard del consumo radio dal punto di vista di ciascun nodo**, con qualità dell'evidenza esplicita.
