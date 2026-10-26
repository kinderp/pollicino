# UC-254 — Osservazioni CO₂ e confronto della ventilazione in aule disconnesse

**Stato:** proposta documentale del 26 ottobre 2026. Nessuna osservazione ambientale raccolta. **Difficoltà:** media (software); medio-alta (misure e protocollo sul campo).

## Problema concreto e user story
Una scuola vuole verificare come cambino le letture di CO₂ durante un'esercitazione didattica prima e dopo una normale apertura delle finestre, senza Internet continuo. Un sensore può misurare, ma i dati trasportati in ritardo potrebbero essere incompleti, provenire da postazioni diverse o essere scambiati per una certificazione della qualità dell'aria. Non bisogna interpretare l'assenza di dati come aria «buona» né automatizzare decisioni di sicurezza a partire da un prototipo.

**User story:** «Come docente, voglio confrontare finestre temporali valide delle letture di due aule, vedere dati mancanti e incertezza, e condividere risultati didattici fra scuole anche con una rete intermittente».

## Attori e rete didattica messinese
Due sensori CO₂ con misura esplicitamente descritta, custodi delle postazioni scolastiche, PC/caches e 4–6 schede LoRa di relay volontari. Prova iniziale in due ambienti scolastici autorizzati (es. Venetico e Rometta), poi possibile replica a Villafranca/Messina. Le stazioni sono fisse e rappresentate da ID di prova, mai dalle persone presenti.

## Perché PollicinoNet e bearer
Il sensore produce finestre numeriche piccole che possono essere recapitate in ritardo via **LoRa** senza streaming. **BLE** può essere usato per configurazione locale; **Wi-Fi/Internet** per serie complete e grafici; **USB/trasporto fisico** per recupero e verifiche indipendenti. Lo store-and-forward mantiene l'informazione sulla finestra osservata anche se la ricezione avviene molto dopo. Usare ove possibile il modello di micro-fatti tipizzati di UC-249.

## Record e limiti interpretativi
Ogni finestra contiene: station_id pseudonimo, inizio e durata, numero di campioni validi/attesi, sensore e versione, stato di verifica/calibrazione, unità, statistiche aggregate, flag di anomalie e ID/hash. Distinguere dati MISURATI, MANCANTI, NON_VERIFICATI e OBSOLETI. Orari di acquisizione, inoltro e visualizzazione sono distinti; l'incertezza temporale deve rimanere visibile. La CO₂ non basta da sola a certificare qualità complessiva dell'aria, sicurezza sanitaria, occupazione o conformità normativa.

## Esperimento software immediato
Generare serie sintetiche per due postazioni con livelli iniziali differenti, fasi di ventilazione simulate, drift del sensore, campioni mancanti, pacchetti duplicati, registri orari divergenti e messaggi fuori ordine. Costruire un confronto solo fra finestre dichiarate compatibili; visualizzare come NON_CONFRONTABILI quelle prive di metadati minimi. Testare che nessun valore mancante diventi zero, che l'arrivo tardivo non sia mostrato come «dato attuale» e che la versione errata di schema sia rifiutata.

Metriche: percentuale di finestre ricostruite/respinte, errori introdotti da timestamp e mancanze, dimensione dei messaggi, ritardo fra osservazione e disponibilità, numero di confronti invalidi bloccati. Tutti i numeri sono sintetici finché non si esegue una vera campagna.

## Hardware reale necessario
Due sensori CO₂ adatti alla didattica (preferibilmente con metodo di misura e procedure di verifica noti), due logger indipendenti, 4–6 schede e PC. Confrontare e documentare la posizione dei sensori, calibrazione/verifica, ventilazione **decisa dai responsabili dell'aula**, finestre di campionamento e condizioni ambientali; non controllare automaticamente finestre, impianti o allarmi. Accettare che un confronto prima/dopo non provi causalità generale senza un disegno sperimentale adeguato. Misurare indipendentemente TX/RX, perdita di finestre, consumo e consegne accettate.

## Privacy, sicurezza e novità
Non raccogliere nomi, presenza, identità o occupazione individuale degli studenti; evitare intervalli troppo granulari che consentano inferenze sugli orari di classe. Conservare i dettagli nella scuola e diffondere solo aggregati autorizzati dopo revisione. Proteggere la provenienza dei sensori e usare autorizzazioni alla pubblicazione; niente pretese di qualità certificata dell'aria. UC-223 riguarda ombra/sole in cortile, UC-242 il rumore, UC-228 il bias da connettività e UC-249 la codifica: **UC-254 definisce un esperimento di ventilazione in ambienti interni con regole esplicite per misure, validità temporale e interpretazioni non ammesse**. Non modifica il PHY congelato.
