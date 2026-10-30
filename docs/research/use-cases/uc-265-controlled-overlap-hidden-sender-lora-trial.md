# UC-265 — Concorrenza di trasmettitori LoRa e ricezioni mancate

**Stato:** proposta del 30 ottobre 2026. Nessun test o risultato radio qui documentato; PHY LoRa congelato invariato.

## Problema risolto

Due relay scolastici potrebbero riuscire a raggiungere lo stesso ricevitore quando trasmettono separatamente, ma perdere alcune ricezioni quando le trasmissioni si sovrappongono. Se ci limitiamo al conteggio dei pacchetti ricevuti, potremmo attribuire erroneamente il problema a distanza, antenna o mobilità. Vogliamo confrontare **finestre con un solo mittente e finestre con due mittenti** usando evidenze indipendenti, senza presumere che ogni perdita sia una collisione o che si possa diagnosticare un vero *hidden terminal* dai soli log.

## Attori, nodi e scenario Messina

Un docente coordinatore; due trasmettitori fissi A/B in posizioni scolastiche autorizzate; un ricevitore principale R; se disponibile un secondo ricevitore di riferimento R2; un collector su PC; 4–6 schede LoRa. Estensione futura fra checkpoint di Villafranca, Rometta, Venetico o Messina, **soltanto dopo** le prove controllate nello stesso complesso scolastico. Gli studenti possono trasportare i log come relay store-and-forward *dopo* la sessione, senza portare trasmettitori attivi in siti non autorizzati.

## Perché PollicinoNet e bearer

La rete di opportunità richiede informazioni attendibili su quali contatti siano realmente utili in presenza di più mittenti. Il catalogo delle capsule permette di recuperare prove in ritardo mantenendole legate al manifest dell'esperimento.

- **LoRa:** trasmissioni sperimentali brevi con identificativi di sessione, mittente, sequenza e profilo radio **già supportato**; eventuali riepiloghi compatti fuori dalla finestra di misura.
- **BLE / USB:** configurazione e lettura dei log locali, senza disturbare il test via LoRa.
- **Wi-Fi / Internet:** raccolta di manifest, cronologie TX/RX e analisi.
- **Trasporto fisico:** scheda, SD o PC consegnano i log quando non c'è backhaul.
- Contratti: `DISCOVERY` annuncia disponibilità delle evidenze; `EXACT` lega manifest/hash, sequenza e log; `SEMANTIC` contiene *ipotesi* (es. `suspected-overlap-loss`), non una diagnosi certa.

## Cosa provare subito senza hardware

Simulatore Python a eventi discreti con TX tentate, TX effettive, intervalli temporali incerti, segnali sovrapposti, RX osservate e log mancanti. Tre scenari: (a) un solo trasmettitore; (b) due trasmettitori a turni; (c) due mittenti con sovrapposizioni **limitate dal budget**. Non fissare una probabilità di collisione come verità della rete; usarla solo come parametro sintetico e confrontare falsi sospetti.

Fixture: TX non eseguita, doppio log, riavvio, orologi disallineati, RX che sente A ma non B, ricevitore di riferimento che osserva diversamente. Calcolare separatamente rapporto RX/TX per ciascun mittente e per ciascuna condizione, dichiarando `UNKNOWN` se mancano i log TX completi. Confrontare differenze con intervalli d'incertezza e riconoscere le variabili confondenti.

## Cosa richiede prove fisiche

1. Verificare prima dispositivo/antenna, configurazione omogenea, canale, frequenza, potenza, sottobanda e condizioni regolamentari realmente applicabili; **non modificare firmware, PHY, MAC o driver**.
2. In ambiente controllato raccogliere per ogni finestra log TX effettive, eventuali ritardi, RX di R e R2, RSSI/SNR se disponibili, uptime e versioni del profilo.
3. Alternare periodi a singolo TX, turni separati e breve concorrenza preautorizzata; mantenere traffico di prova minimo ed entro il budget.
4. Se l'adapter non consente una verifica attendibile della temporizzazione, classificare la sovrapposizione come `UNKNOWN` invece di forzare conclusioni.
5. Ripetere soltanto in siti fissi autorizzati; non cercare o provocare interferenze ad altri utenti dello spettro.

**Misure richieste:** denominatore di TX realmente effettuate, ricezioni indipendenti, grado verificabile di sovrapposizione, errori/assenze di log, configurazione e variabilità fra ripetizioni. Nessun PDR, raggio, throughput o beneficio di scheduling è attualmente misurato.

## Privacy, sicurezza e difficoltà

Campagne con pseudonimi temporanei, **nessun GPS o percorso individuale**, dataset sintetici e nessuna graduatoria degli studenti. Manifest firmato, scadenza, campagna isolata (UC-256), stop locale, tetto di airtime e conservazione breve dei log. Non testare forme di jamming. **Difficoltà medio-alta/alta** (strumentazione e causalità).

## Differenza dai casi esistenti

UC-063 osserva lo spettro; UC-196 confronta ricevitori; UC-226 coordina campagne concorrenti; UC-231 contabilizza il budget; UC-232 misura il link nei due versi; UC-259 studia previsioni territoriali e UC-263 ripetibilità dopo pioggia. **UC-265 isola l'effetto della concorrenza di più mittenti sul medesimo ricevitore**, con baseline appaiate e guardie contro l'attribuzione indebita della causa.

## Gate di accettazione (futuri, non eseguiti)

- Il test software distingue `TX_NOT_SENT`, `TX_SENT_NO_RX`, `RX_OBSERVED`, `LOG_INCOMPLETE`; nessuna statistica con denominatore inventato.
- A e B restano separati in tutte le analisi; i log ritardati non contaminano altre campagne.
- La reportistica separa sovrapposizione osservata, sovrapposizione stimata e causa ignota.
- La campagna fisica non è dichiarata valida senza evidenza TX e RX indipendente e verifica dei limiti radio.
