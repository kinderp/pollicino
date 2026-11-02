# UC-275 — Quanto valore aggiunge LoRa? Campagna con controllo senza LoRa

**Stato:** proposta del 2 novembre 2026; nessun benchmark eseguito, nessuna misura fisica disponibile. **Difficoltà:** medio-alta (controllo sperimentale e metriche applicative). Il PHY LoRa congelato rimane intatto; nessun cambio a MAC, driver o firmware.

## Problema concreto e user story

Una scuola pubblica un piccolo kit di esercizi o un inventario di sensori a Messina. Un'altra sede a Rometta lo deve ricevere **entro l'inizio della lezione**. PollicinoNet usa LoRa per indizi e, se opportuno, per capsule minuscole; tuttavia lo stesso materiale potrebbe arrivare comunque quando i PC si incontrano su Wi-Fi o quando qualcuno porta una chiavetta USB. **Non possiamo attribuire a LoRa un beneficio semplicemente perché il trasferimento è riuscito.**

**Come docente sperimentatore**, voglio confrontare la disponibilità del servizio **con e senza LoRa**, a parità di oggetti, opportunità di contatto, vincoli e scadenza; voglio poter concludere anche `NO_DEMONSTRATED_BENEFIT` o `INCONCLUSIVE`.

## Attori e scenario messinese

Due o tre checkpoint scolastici autorizzati (ad esempio Messina, Villafranca, Rometta, Venetico), cache su PC, un collector indipendente, 4–8 schede e, solo dopo il banco fisso, relay volontari degli studenti in **store-and-forward**. Niente raccolta di posizione, tragitti, frequenza di presenza o identificativi permanenti dei volontari. Materiali tutti fittizi e redistribuibili.

## Varianti di confronto predefinite

- **C0 — controllo senza LoRa:** scambio solo al contatto già disponibile su BLE/Wi-Fi/LAN/USB, con le medesime cache.
- **C1 — LoRa di controllo:** indizio/need/avviso compatto su LoRa; oggetto completo su bearer ricco o trasporto fisico.
- **C2 — LoRa per contenuto piccolo ammesso:** oltre alla discovery, invio di una capsula **solo se già supportata, lecita e entro budget**, altrimenti dichiarare `NOT_SUPPORTED` e non alterare il PHY.

Eseguire coppie di campagne su identiche fixture di oggetti e scadenze, randomizzando/counterbilanciando l'ordine delle condizioni; **nelle campagne fisiche** i contatti non sono replicabili perfettamente, dunque registrare differenze ed evitare conclusioni causali se non comparabili. In simulazione usare **le stesse** trace di contatto predefinite per C0/C1/C2; non presentare il simulatore come una misura del mondo reale.

## Contratto dati e perché PollicinoNet

`campaign_id, treatment, artifact_id/hash, size, publication_time, deadline, checkpoint_id, planned_contact_window, observed_contact, transfer_attempt, actual_tx, rx_log_status, exact_acceptance_receipt, byte_count_by_bearer, clock_uncertainty`. Il risultato deve distinguere `NOT_REACHED`, `REACHED_UNVERIFIED`, `EXACT_ACCEPTED_ON_TIME`, `ACCEPTED_LATE`, `UNKNOWN_LOG`; la sola ricezione radio non prova consegna applicativa.

PollicinoNet è adatto perché conserva/rilancia eventi e oggetti fra partizioni. Il test però misura **il suo valore incrementale**, non presume che quel valore sia sempre positivo. Separare `DISCOVERY` da `EXACT`; `SEMANTIC` non è una consegna identica dei byte.

## Bearer

- **LoRa:** avvisi, need, piccoli ricevute/ticket e, solo se ammissibili, capsule brevi nelle varianti abilitate.
- **BLE:** handoff di prossimità e inventari autorizzati.
- **Wi-Fi/Internet:** consegna del kit/manifest e collector, dove presenti; registrare quando Internet è indisponibile.
- **USB/SD/trasporto fisico:** controllo naturale non radio, con stessa verifica SHA-256 e stesso deadline.

## Prove software immediate

Simulatore a eventi con 3 checkpoint, 6 relay virtuali e 40 oggetti fittizi (alcuni già nei cache, alcuni mancanti), contatti brevi, contatti mancati e disconnessioni. Criteri automatici:
1. C1/C2 non sono dichiarati migliori quando C0 consegna entro scadenza con minor costo;
2. un indizio LoRa non conta come oggetto ricevuto; una ricevuta dell'applicazione sì, se verificata;
3. missing TX/RX log => risultato `UNKNOWN` anziché PDR inventato;
4. tempi e byte per bearer sono aggregati senza sommare due volte lo stesso artefatto;
5. scenari con LoRa inefficace, sovraccarico o senza contatto restituiscono `NO_DEMONSTRATED_BENEFIT/INCONCLUSIVE`;
6. stesso scenario/seed dà una metrica deterministica e auditabile.

**Output software:** differenza nella percentuale di checkpoint `EXACT_ACCEPTED_ON_TIME`, latenza con intervalli/incertezza, byte e airtime **simulato** per bearer, costo energetico modellato separatamente, disponibilità/incompletezza degli evidenziari. Non dichiarare misure fisiche o benefici prima di un esperimento reale.

## Gate e prove fisiche

Prima verificare inventario reale degli adapter/capacità, regolazione delle sotto-bande, limiti di duty cycle, antenna/alimentazione, clock, budget radio e comportamento di stop locale. Partire con due PC isolati e 4 schede fra **due postazioni fisse**, senza spostamenti di minori; confrontare prove counterbilanciate C0/C1 e, se già supportata, C2. Raccogliere TX osservate dal mittente, RX indipendenti e accettazioni EXACT sul ricevente; ripetere in più sessioni. Solo poi utilizzare, con consenso istituzionale, relay nello zaino in normali spostamenti, senza tracciare chi/come/dove.

Il risultato fisico deve riportare **intervalli di incertezza**, cambiamenti di condizioni e eventuali fattori confondenti, non affermare superiorità della tecnologia senza prova appaiata.

## Sicurezza, privacy, differenze

Firmare il manifest di campagna e verificare artefatti/permessi; impedire che vecchie code di altre campagne falsino i conteggi. Tutto sintetico, nessun dato di studenti né voti. Il collector può archiviare solo checkpoint pseudonimi e conteggi aggregati.

**UC-183** confronta politiche di routing su link reali/shadow; **UC-124** sceglie bearer in runtime; **UC-188** studia se un contatto possa completare un payload; **UC-266** misura equità delle lezioni; **UC-256** isola campagne. **UC-275 introduce un vero braccio di controllo *senza LoRa*, necessario per quantificare il contributo causale (oppure nullo/inconclusivo) del bearer scarso**.
