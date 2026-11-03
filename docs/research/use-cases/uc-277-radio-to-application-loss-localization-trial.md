# UC-277 — Diagnosi delle perdite tra ricezione LoRa e applicazione

**Stato:** proposta documentale del **3 novembre 2026**; non implementata, nessun test software né misura fisica eseguiti. **Difficoltà:** medio-alta. PHY LoRa congelato, MAC, driver e firmware **non vengono modificati**.

## Problema concreto e user story

Due schede scolastiche sembrano comunicare male: il programma sul PC di Rometta conta 70 capsule ricevute su 100 annunciate dal mittente di Venetico (numeri **puramente illustrativi**, non misurati). Ma i 30 oggetti mancanti potrebbero non essere stati trasmessi, non essere stati decodificati via radio, essere stati persi fra la scheda e il programma host (coda, seriale/USB, parsing), oppure essere stati ricevuti ma respinti dall'applicazione per firma o schema. Una sola percentuale `RX_app/TX_requested` confonde fenomeni distinti.

**Come docente del testbed** voglio sapere **in quale tratto osservabile si interrompe il percorso**, e ottenere `UNKNOWN` dove manca strumentazione, prima di cambiare il routing o attribuire perdite alla propagazione radio.

## Attori, nodi e scenario Messina

- Docente responsabile e collector con manifest di campagna.
- Uno o due trasmettitori LoRa di prova, un ricevitore gestito e, se disponibile, un ricevitore indipendente di riferimento: inizialmente 3–4 schede su banco autorizzato, poi 4–8 a postazioni fisse di Messina, Villafranca, Rometta, Venetico.
- Uno o due PC host con adapter **già disponibile** e registrazione dei soli contatori che effettivamente espone; relay volontari store-and-forward per scambiare log tra sedi dopo le prove (non per localizzare gli studenti).

PollicinoNet collega la catena `DISCOVERY -> trasferimento -> EXACT -> accettazione applicativa`: la prova distingue la comunicazione radio dalla catena locale radio/host/app. **Non è prevista alcuna nuova modifica di PHY, timing o driver**.

## Bearer e contratto di prova (applicativo)

- **LoRa:** capsule sintetiche minime entro i limiti **effettivi** dell'adapter e il budget di trasmissione, con `campaign_id`, `seq`, `object_id`; nessuna forzatura di frequenza/potenza.
- **BLE e USB/seriale:** raccolta dei contatori diagnostici lato nodo e trasferimento locale dei log **solo se già esposti**. Se il firmware non espone ricezioni radio grezze, NON inventare un contatore.
- **Wi-Fi / Internet:** raccolta differita, confronto e analisi dei log.
- **SD / trasporto fisico:** portare manifest e log firmati fra checkpoint; non utilizzare chiavette sconosciute o eseguire file ricevuti automaticamente.

Schema di **evento di audit**, non wire-format: `{campaign_id, station_role, device_pseudonym, seq, stage, time_or_uncertainty, evidence_source, software_version, status}`. Stage candidati: `TX_REQUESTED`, `TX_CONFIRMED_IF_EXPOSED`, `RX_RADIO_IF_EXPOSED`, `RX_ADAPTER`, `RX_HOST`, `PARSE_ACCEPTED`, `EXACT_ACCEPTED`, `APP_ACCEPTED`, `UNKNOWN`. Una conferma di scrittura seriale non prova una TX in aria; la presenza su host non prova la decodifica RF indipendente. `RX_RADIO` è registrabile soltanto quando la piattaforma fornisce una prova attendibile a quel livello, senza richiedere modifiche proibite.

## Esperimento immediato senza hardware

1. Costruire un simulatore a eventi discreti a **sei fasi** e fixture riproducibili: 100 oggetti sintetici con seed e idempotenza.
2. Iniettare **separatamente** mancata TX, perdita sul collegamento, overflow di una coda host, riga seriale troncata, parsing rifiutato, hash errato e ricevuta applicativa duplicata.
3. Ripetere con log mancanti, riavvio del PC, timestamp fuori ordine e richieste duplicate; distinguere `NOT_OBSERVED` da `OBSERVED_DROPPED`.
4. Calcolare tassi condizionati **solo** dove denominatore e fase precedente siano osservabili; altrimenti `INCONCLUSIVE` e limite inferiore/superiore, non una diagnosi arbitraria.
5. Confrontare un report ingenuo end-to-end con il report per fasi e salvare i seed, la versione del parser e lo stato `PASS/FAIL/UNKNOWN/NOT_TESTED`.

**Criteri PASS proposti:** nessun guasto seriale attribuito al PHY quando il ground truth sintetico lo colloca nell'host; nessun `APP_ACCEPTED` per hash/permesso errato; nessun tasso fisico stimato da `TX_REQUESTED` in assenza di misura TX.

## Prove fisiche (non eseguite)

A banco: inventario hardware, antenne identiche, alimentazione controllata, log clock/uncertainty, una campagna A/B con programma host normale e programma host intenzionalmente rallentato **senza cambiare firmware/driver**. L'esperimento sotto carico resta entro frequenze, potenze e duty-cycle consentiti; mai generare interferenza deliberata. Usare ricevitore indipendente quando disponibile per confronto TX/RX, ed etichettare `UNKNOWN` ogni stadio non osservabile. Trasferire in differita i log mediante un secondo bearer. Solo successivamente confrontare due checkpoint provinciali con posizioni fisse e consenso; mai traiettorie individuali.

Misure da produrre sul campo: numero di eventi effettivamente osservati a ciascuno stadio, record incompleti, drop applicativi classificati, byte nei log, intervalli e ricevute EXACT. Nessuna ipotesi di PDR, copertura, throughput, potenza o autonomia senza dati acquisiti e denominatori validi.

## Privacy, sicurezza e limiti

ID di campagna temporanei, dati artificiali, nessuna posizione personale, niente ID hardware permanenti nei report pubblici, log a conservazione limitata con firme/hash e ruoli di accesso. Non trasformare la visibilità delle diagnostiche in un canale di sorveglianza. Evitare di esporre segreti nei log. L'osservabilità di `RX_RADIO` e `TX_CONFIRMED` dipende dalle capacità attuali della scheda/adapter: **se mancano, il test rimane un audit software/host e non una diagnosi radio**.

## Differenza dai casi esistenti

**UC-265** confronta TX singole/concorrenti e osservazioni RF; **UC-178** impedisce denominatori distorti quando mancano log; **UC-221** separa consegna e accettazione; **UC-230** verifica la conformità fra bearer. **Questo caso isola la perdita interna nella catena nodo-adapter-host-parser-applicazione**, misurando quali fasi siano visibili e proibendo inferenze sul PHY da un semplice contatore applicativo.

## Fonti di metodo (non risultati PollicinoNet)

- Microchip, *UART Overrun Error May Occur and Go Unreported Without Flow Control*: https://onlinedocs.microchip.com/oxy/GUID-10C0900B-7F32-4ACD-A6A3-4ADA93D06BD6-en-US-5/GUID-09740EE4-ABEC-488D-B718-053762E6DC60.html — esempio di perdita a valle del ricevitore in un componente differente; non prova un difetto nelle schede PollicinoNet.
