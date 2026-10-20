# UC-232 — Prova appaiata dell'asimmetria dei collegamenti LoRa

**Stato:** proposta documentale, 2026-10-20; nessuna misura fisica eseguita.

## Problema
Se A riceve B, possiamo dare per scontato che B riceva A? No: alimentazione, sensibilità, antenna, interferenze e geometria possono produrre risultati diversi. Un algoritmo che presume collegamenti bidirezionali rischia di scegliere relay incapaci di inviare risposte o ricevute.

## Attori e scenario Messina
Due schede a postazione fissa A/B e uno o due ricevitori-testimoni, tecnico e gruppo di studenti. Prove iniziali in laboratorio; dopo autorizzazione, checkpoint scolastici fra Messina e Venetico. Evitare qualunque inferenza su tragitti dei partecipanti.

## Perché PollicinoNet e bearer
**LoRa** trasporta sequenze di prova compatte, prima in una direzione e poi nell'altra con stesso assetto e condizioni dichiarate. **BLE/Wi-Fi** trasferisce i log completi; **USB/SD** li recupera anche senza Internet. Lo store-and-forward può portare tardivamente i log di un lato al collector. Una mancata ricevuta non va confusa con mancata ricezione: il denominatore è il numero di trasmissioni di cui abbiamo evidenza.

## Esperimento software immediato
Simulare collegamenti A→B e B→A con probabilità di successo differenti, trasmissioni non effettuate, log mancanti e perdita di ricevute. Generare serie `ABBA`/ordine controbilanciato e report direzionali: tentativi osservabili, messaggi ricevuti, intervalli di confidenza e `UNKNOWN` dove mancano log. Un test automatizzato deve rilevare l'asimmetria sintetica senza confondere direzione con ordine temporale.

## Prova fisica necessaria
Almeno 4 schede (coppia e testimoni) e due postazioni consentite. Fissare orientamento, altezza, alimentazione, configurazione radio e distanze; invertire la direzione in blocchi ripetuti, poi scambiare fisicamente i dispositivi per distinguere difetto dell'hardware da effetto del luogo. Misurare trasmissioni effettive, ricezioni, RSSI/SNR disponibili e incertezza. Nessuna previsione di copertura o PDR fisico prima delle prove.

## Sicurezza/privacy e difficoltà
Solo payload casuali e ID di laboratorio; nessun identificativo permanente dello studente. Rispetto delle condizioni radio applicabili e sospensione locale immediata. **Difficoltà: media** per il software; **medio-alta** per il disegno sperimentale. Esito atteso: rapporto A→B/B→A con limiti dell'evidenza, non una mappa di copertura inventata.

## Originalità rispetto al catalogo
UC-196 confronta più ricevitori per un trasmettitore; UC-211 isola il montaggio nello zaino; UC-188 valuta la trasferibilità dell'oggetto. **UC-232 misura esplicitamente la direzionalità del collegamento appaiando le trasmissioni nei due sensi**.
