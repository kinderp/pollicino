# UC-283 — Checkpoint LoRa e involucro dell'edificio scolastico

**Data/stato:** 5 novembre 2026; **proposta documentale**, non implementata e senza dati fisici. Difficoltà **medio-alta**. PHY LoRa congelato, MAC, driver e firmware **invariati**.

## Problema concreto e obiettivo

Prima di predisporre una rete di checkpoint nella provincia di Messina occorre scegliere dove collocare un relay fisso: dentro il laboratorio, vicino a una finestra o in un punto esterno autorizzato. Un test fra due postazioni non dimostra automaticamente che il nodo possa restare al chiuso. Vogliamo **misurare se e in quali condizioni una postazione scolastica realmente configurata riesca a scambiare capsule**, senza inventare un valore di attenuazione o una copertura geografica.

**User story:** come docente che vuole ospitare un nodo a Rometta, desidero una decisione riproducibile tra tre posizioni *consentite* prima di coinvolgere relay volontari nell'hinterland Messina–Villafranca–Rometta–Venetico.

## Attori, nodi, perché PollicinoNet

Docente e responsabile edificio; due checkpoint autorizzati, schede LoRa TX/RX, idealmente ricevitore indipendente di riferimento, due PC per log; relay studenti volontari solo in fase successiva. PollicinoNet è adatto perché la rete **store-and-forward** può usare una postazione disponibile solo in alcune finestre: conta l'esito della **capsula verificata dall'applicazione**, non una stima arbitraria di RSSI o la sola presenza di un segnale.

Non chiediamo ai minori di tenere un registro degli spostamenti né di installare antenne su tetti o facciate. Un eventuale nodo esterno si usa soltanto con permessi, alimentazione sicura e postazione stabile.

## Bearer e contratto informativo

- **LoRa:** piccoli identificativi di campagna, sequenze di prova e capsule già compatibili con l'adapter; niente modifica a PHY/MAC, nessuna assunzione sul payload massimo.
- **BLE:** scarico dei piccoli log e configurazione locale, se già supportati.
- **Wi-Fi/LAN/Internet:** sincronizzazione dei log completi e verifica applicativa quando disponibili; non usarli per attribuire alla radio una consegna LoRa.
- **USB/SD e trasporto fisico:** recupero dei log dopo una partizione e confronto fra siti.
- **DISCOVERY:** opportunità di scambio osservata; **EXACT:** ID prova + hash della capsula e receipt verificata; **SEMANTIC:** «dentro», «finestra», «esterno», soltanto etichette della postazione.

Una ricevuta applicativa non equivale a «copertura garantita»; conteggiare i tentativi solo quando i log TX li confermano (UC-178/277).

## Test immediato in software (non ancora eseguito)

1. Generare uno script di 4 blocchi **ABBA** con tre configurazioni, TX schedulati e log sintetici contenenti TX noti, RX, hash EXACT, app acceptance, interferenze simulate e ingressi incompleti.
2. Costruire un parser che separi `TX_CONFIRMED`, `RX_SEEN`, `APP_ACCEPTED`, `NO_RX_OBSERVED`, `UNKNOWN_TX_OR_LOG`: nessun «PDR=0» se il denominatore TX non è noto.
3. Confrontare A/B soltanto quando configurazione radio, antenna, orientamento, distanza e strumento di misura risultano documentati; segnalare i cambiamenti di variabili come `NOT_COMPARABLE`.
4. Simulare un relay che riceve la capsula, si spegne, la conserva e la inoltra più tardi; verificare l'esattezza dell'oggetto e la distinzione tra consegna radio e applicativa (UC-253/221).
5. Generare report esplicitamente marcati `SIMULATED` con seed, test missing log, differenze per blocco e intervalli descrittivi; nessuna conclusione su edifici reali.

**Criteri verificabili:** nessun conteggio con denominatore ignoto; nessun `APP_ACCEPTED` senza ricevuta; confronto rifiutato se il contesto sperimentale non è allineato; stessa fixture sintetica produce lo stesso report.

## Prova con schede reali e misure ancora necessarie

Primo passo: **4–6 schede** e due PC nel cortile/laboratorio scolastico, su posizioni fisse approvate. Provare in sessioni alternate: A) postazione esterna sicura, B) presso finestra interna, C) all'interno dell'aula. Stabilire prima una distanza e orientamento ragionevoli, verificare se le finestre aperte/chiuse costituiscono condizioni separate; replicare più blocchi, non una singola prova. Registrare impostazioni immutate, antenne, alimentazioni, tempo, numero TX realmente emessi, RX realmente osservati e capsule/hash applicativi accettati, oltre a mancate osservazioni. Analizzare solo ciò che la strumentazione espone.

Poi, se autorizzati, ripetere su **due checkpoint scolastici** nell'area Messina–Villafranca–Rometta–Venetico con relay store-and-forward volontari. Non riportare distanze coperte o perdite «misurate» prima che i log reali esistano. Verificare previamente sottobanda, potenza, duty-cycle, antenna e normativa applicabili.

## Privacy, sicurezza e difficoltà

Usare nomi di siti aggregati e ID di prova effimeri; nessuna mappa di casa, posizione esatta degli studenti, orari individuali o foto di persone. Solo luoghi scolastici e autorizzazioni del gestore; niente lavori elettrici/improvisati in quota, niente prove durante temporali o su infrastrutture pubbliche. Controlli di accesso ai log; invio con budget radio. **Difficoltà medio-alta:** il codice di report è semplice, il confronto fisico replicabile è difficile.

## Anti-duplicazione

**UC-211** confronta montaggi/posizioni dell'antenna sul nodo; **UC-280** verifica l'abitacolo di un veicolo parcheggiato; **UC-259** calibra previsioni orografiche; **UC-232** confronta direzioni radio; **UC-277** separa perdita radio e host. **UC-283** introduce il *gate per la collocazione operativa del checkpoint dentro un edificio scolastico* e confronta esplicitamente tre posizioni autorizzate con esito applicativo. Riutilizza la loro metodologia; non afferma una nuova proprietà del PHY.

## Riferimenti per metodo, non risultati PollicinoNet

- [Misure di propagazione LoRa a 868 MHz in ambiente indoor, Sensors 2023](https://doi.org/10.3390/s23063283). Il lavoro non prevede la copertura delle nostre postazioni.
- [Bundle Protocol Version 7, RFC 9171](https://www.rfc-editor.org/rfc/rfc9171.html) per il contesto delle reti a consegna differita; non implica che PollicinoNet implementi BPv7.
