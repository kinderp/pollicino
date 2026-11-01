# UC-271 — Alimentazione USB/powerbank e auto-disturbo: prova radio appaiata

**Stato:** proposta documentale del **1 novembre 2026**. Non implementata; nessuna misura fisica eseguita. **Difficoltà:** medio-alta. **Invarianti:** PHY LoRa congelato, MAC, driver e firmware invariati.

## Problema e storia concreta

Una scheda funziona sul banco con alimentazione USB, ma quando uno studente la alimenta con un powerbank nello zaino sembra ricevere meno messaggi. Non sappiamo se la causa sia l'alimentazione, il posizionamento dell'antenna, un contatto perso, il duty cycle o un log incompleto. Prima di distribuire molte schede nei comuni messinesi, vogliamo **separare l'effetto osservato da una causa soltanto ipotizzata**.

**User story:** come docente del testbed provinciale voglio confrontare la stessa coppia radio in condizioni di alimentazione differenti, in prove appaiate e ripetibili, senza modificare la radio, per capire se le differenze osservate meritino ulteriori indagini. Un risultato negativo è utile quanto uno positivo.

## Attori, nodi e perché PollicinoNet

Docente responsabile, 4–6 schede LoRa di prova (inizialmente due trasmittenti e due ricevitori di riferimento), alimentatori USB/powerbank **sicuri e compatibili**, collector e successivamente relay volontari. I checkpoint autorizzati possono essere a Rometta, Venetico e Villafranca; durante il confronto A/B si utilizzano **postazioni fisse**, senza registrare i tragitti degli studenti.

I nodi PollicinoNet potranno scambiarsi in differita **schede di prova compatte e digest**; i risultati completi arrivano via bearer più capiente. Questa campagna verifica una dipendenza fisica del servizio store-and-forward: il ricevitore può perdere opportunità anche se la coda applicativa funziona. Non si presume che un powerbank causi disturbi RF: è **un'ipotesi da testare**.

## Bearer

- **LoRa:** poche capsule di prova con `campaign_id`, sequenza e payload compatibili con l'adapter attuale. Nessuna nuova modalità PHY, timing MAC o trasmissione ad alto volume.
- **BLE:** acquisizione locale autorizzata dei contatori e delle informazioni di sessione, se supportato.
- **Wi-Fi / Internet:** trasferimento e analisi dei log, quando disponibili.
- **USB/SD / trasporto fisico:** recupero esatto dei log e inventario delle alimentazioni da postazioni isolate.

## Contratto minimo dell'esperimento

Manifest versionato: `campaign_id`, `device_pseudonym`, `receiver_id`, `power_source_class` (senza matricole identificanti), `trial_order`, `radio_config_hash`, `firmware_hash`, `antenna_mount_id`, `planned_tx`, `confirmed_tx`, `observed_rx`, `log_completeness`, `window_start/end`, `uncertainty_flags`. Separate le richieste di trasmissione dalle trasmissioni **effettivamente eseguite** e dalle ricezioni confermate dai ricevitori indipendenti.

Prova crossover A/B/A/B o ordine bilanciato e, quando possibile, randomizzato; stesso hardware radio, posizione, antenna, payload, fascia temporale confrontabile. Pre-registrare numero massimo di trasmissioni e regole di arresto. Classificare il risultato `OBSERVED_DIFFERENCE`, `NO_DETECTABLE_DIFFERENCE` o `INCONCLUSIVE`. **Non usare `EMI_CONFIRMED` senza indagini elettriche/RF indipendenti**: variazioni di PDR o SNR non ne dimostrano la causa.

## Cosa provare subito senza hardware

Simulare due condizioni di alimentazione, due ricevitori e quattro sessioni appaiate con valori artificiali, log persi, trasmissioni richieste ma non eseguite, un'antenna spostata e un cambio di firmware. Un analizzatore Python deve:

1. rifiutare il confronto quando configurazione o montaggio differiscono senza controllo;
2. usare il denominatore di TX realmente eseguite, segnalando la copertura dei log;
3. restituire `INCONCLUSIVE` in presenza di evidenze insufficienti;
4. non attribuire causalmente alla sorgente USB qualunque perdita;
5. produrre un report riproducibile per sessione, con statistiche descrittive e incertezza.

**PASS software:** i controesempi sintetici non generano conclusioni causali o misure fisiche finte; sessioni con etichetta errata o incomplete non sono confrontate come valide. Nessuna implementazione o test eseguito in questa proposta.

## Prove hardware necessarie

Banco iniziale con 4 schede (due sorgenti radio, due ricevitori di riferimento), log indipendenti e strumenti di misura energetica **idonei**. Provare solo alimentatori e cavi approvati con tensione/corrente corrette; non aprire powerbank, non cortocircuitare, non scollegare antenne durante TX. Cambiare **una variabile alla volta**. Misurare TX effettive, RX per ricevitore, RSSI/SNR quando realmente esposti dall'adapter, reboot/brownout, potenza assorbita se misurabile, e completezza dei log. Un'eventuale analisi di disturbi condotti/irradiati richiede strumentazione e competenze specifiche; altrimenti riportare solo correlazioni osservate.

Dopo il banco, ripetere su due checkpoint autorizzati e poi in una rete provinciale con relay volontari, ma **non confrontare alimentazioni mescolando condizioni mobili e fisse**. Frequenza, potenza, antenne e tempo in aria devono rispettare le condizioni radio applicabili in Italia alla configurazione effettiva.

## Privacy e sicurezza

Niente nominativi, coordinate o percorsi degli studenti; identificativi effimeri per campagna, log a conservazione limitata, raccolta di partecipazione volontaria con stop immediato. Firmware e rapporti firmati/hashati, profili di riferimento immutabili; vietato generare interferenze intenzionali.

## Perché non è un duplicato

- **UC-206** verifica la prontezza della scheda, **UC-211** il montaggio dell'antenna; qui l'**unica variabile manipolata è la classe di alimentazione**, con disegno crossover e classificazione causale prudente.
- **UC-214** segue l'umidità dell'involucro; **UC-263** ripete misure dopo pioggia; **UC-265** esamina trasmettitori concorrenti. Nessuno isola il confronto USB/powerbank su postazioni identiche.
- **UC-178/228** insegnano l'audit dei denominatori e del bias; UC-271 li **riusa**, senza reinventarli.

**Output atteso:** un protocollo di prova appaiata e dati reali solo dopo misurazione. Nessun risultato di PDR/copertura/autonomia è qui dichiarato.
