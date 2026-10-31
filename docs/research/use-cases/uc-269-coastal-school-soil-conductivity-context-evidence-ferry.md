# UC-269 — Suolo degli orti scolastici: conducibilità, umidità e interpretazione differita

**Stato:** proposta documentale del 31 ottobre 2026. Nessuna lettura fisica acquisita e nessuna diagnosi di salinizzazione del territorio. PHY LoRa congelato invariato. **Difficoltà:** media-alta (qualità delle misure più impegnativa del trasporto).

## Problema risolto e storia concreta

Un sensore economico segnala un cambiamento di conducibilità elettrica (EC) del terreno di un orto scolastico vicino alla costa. Il valore **non basta** a concludere che sia aumentata la salinità: umidità, temperatura, composizione del suolo, metodo e calibrazione possono alterare l'interpretazione. Le scuole senza collegamento permanente vogliono confrontare osservazioni **contestualizzate** anziché trasmettere un numero isolato.

**User story:** come gruppo di Scienze/Informatica voglio raccogliere osservazioni di suolo ripetibili da più orti e riunificarle in differita, mantenendo distinta la lettura strumentale dall'ipotesi scientifica.

## Attori, nodi e scenario Messina

Due orti/cortili scolastici fissi e autorizzati a Rometta e Venetico (eventuale terza postazione a Spadafora, dopo verifica); docenti di Scienze, studenti, sensori EC/umidità/temperatura idonei, collector su PC, 4–6 schede LoRa come relay e una stazione di riferimento per verifiche. I relay volontari degli studenti possono portare **soltanto riepiloghi non personali** fra due checkpoint; niente misura in proprietà private né localizzazione di studenti.

## Perché PollicinoNet e bearer

Gli strumenti producono serie lentamente variabili: non richiedono Internet continuo. Lo store-and-forward consente di portare prima il digest di una finestra valida e più tardi la serie, allegati e protocolli di calibrazione.

- **LoRa:** piccoli eventi `observation_window_ready` con ID del sito scolastico, finestra, schema/versione, hash e stato qualità, solo se il payload effettivo lo consente.
- **BLE:** lettura del sensore e sincronizzazione locale nei pressi del checkpoint.
- **Wi-Fi / Internet:** trasferimento delle serie, grafici e tabelle di riferimento.
- **USB / SD / trasporto fisico:** evidenze complete o esportazioni da PC isolati.
- **DISCOVERY** annuncia osservazioni; **EXACT** recupera serie e protocollo con hash; **SEMANTIC** conserva ipotesi come `POSSIBLE_CHANGE`, mai una certificazione ambientale.

## Modello dati minimo

`site_pseudonym`, `window_start`, `clock_quality`, `sample_count_expected/actual`, `sensor_model`, `sensor_revision`, `method_id`, `depth_class`, `ec_value`, `ec_unit`, `moisture_value`, `temperature`, `calibration_ref`, `quality_flag`, `source_hash`. Conservare il significato esatto delle unità e distinguere **EC apparente del suolo** da misure della soluzione estratta: non sono direttamente intercambiabili. Nessuna correlazione fra due siti dimostra da sola una causa comune.

## Test software immediato (senza hardware)

Simulare 90 giorni di osservazioni sintetiche per tre siti; introdurre periodi secchi/umidi, deriva, sensore sostituito, timestamp inaffidabili, campioni assenti e trasferimenti fuori ordine. Generare annunci compatti e oggetti `EXACT` firmati; riconciliare i dati per **tempo di acquisizione**, non arrivo. Il rapporto deve rifiutare confronti fra unità/metodi incompatibili e distinguere dato assente, lettura guasta e misura confermata.

**Criteri PASS:** nessuna interpolazione presentata come misura; nessun allarme «intrusione marina» dai soli numeri; intervalli incompleti evidenziati; controlli di integrità e provenienza applicati; conteggio dei bytes per bearer; confronto di metodi corretto o `NOT_COMPARABLE`.

## Prove fisiche necessarie

1. Verificare reperibilità, sicurezza e caratteristiche dei sensori; prima test co-localizzato su un medesimo campione, ripetibilità e procedura documentata con controllo di riferimento adeguato.
2. Selezionare due siti scolastici autorizzati con protocolli omogenei di profondità, intervallo e condizioni di misura; raccogliere metadati di metodo, temperatura/umidità e campioni di controllo.
3. Trasportare via LoRa solo annunci e piccoli riepiloghi; inviare serie complete via BLE, Wi-Fi o USB quando possibile.
4. Misurare consegne effettive, ritardi, missingness, stabilità della strumentazione e divergenze fra metodi; se si intende parlare di salinità, richiedere appropriata verifica da campioni e consulenza scientifica, non inferirla dalla sola EC.

Le postazioni costiere/interno devono essere intese come **confronto didattico controllato**, non monitoraggio ambientale ufficiale o diagnosi per agricoltori.

## Privacy, sicurezza e difficoltà

Solo siti istituzionali con autorizzazione, identificativi di postazione e non di studenti; niente coordinate di persone né dati su proprietà private. Integrità dei dati, firme dei manifest, accesso autorizzato per allegati, durata limitata dei log. L'osservazione non attiva automaticamente irrigazione, trattamenti o avvisi pubblici.

## Anti-duplicazione

- **UC-003/116:** trasporto sensori e citizen science generici; qui l'unità scientifica è **EC + umidità + temperatura + metodo + qualità**, con confronto *non automaticamente interpretabile*.
- **UC-031/166:** calibrazione del sensore; qui calibrazione è una dipendenza, l'obiettivo è impedire conclusioni scorrette da EC non comparabili.
- **UC-146/191:** bisogni irrigui e bilancio idrico; qui non si gestiscono risorse o decisioni irrigue.
- **UC-171:** qualità di acqua costiera; qui si misura il **suolo di orti scolastici**, non l'acqua.
- **UC-254/264/267:** altre osservazioni ambientali; non coprono questo particolare protocollo scientifico.

Riferimento di contesto (non misure locali): [Studio sugli effetti di umidità, tessitura e caratteristiche del suolo sulla conducibilità apparente](https://portal.fis.tum.de/en/publications/influence-of-soil-properties-on-electrical-conductivity-under-hum/).
