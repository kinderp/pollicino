# UC-242 — Osservatorio didattico del rumore ambientale senza audio personale

**Stato:** proposta documentale del 22 ottobre 2026; nessuna misura eseguita. **Difficoltà:** medio-alta.

## Problema e storia d'uso
Confrontare finestre di rumore ambientale in alcuni cortili o postazioni fisse è interessante, ma una trasmissione continua di audio rischierebbe di catturare persone, consumare banda e produrre dati difficili da interpretare. Si vuole trasportare **solo un riepilogo numerico** e le informazioni sulla qualità della misura, anche dopo ore di isolamento.

**Scenario Messina:** due postazioni didattiche autorizzate, una in un cortile di Venetico e una in un cortile di Messina, producono campioni su finestre temporali predefinite. Relay scolastici recuperano riepiloghi firmati; un docente confronta finestre effettivamente comparabili. La collocazione serve come contesto di **stazione fissa**, non come tracciamento.

## Attori e perché PollicinoNet
Sensore microfonico con elaborazione locale, operatore di stazione, relay store-and-forward, revisore scientifico e cache. PollicinoNet è adatto a finestre di dati compatte e differibili, non a streaming di registrazioni. Record proposto: station_pseudonym, window_start, duration, sample_coverage, noise_proxy, calibration_status, sensor_profile, digest e quality_flags.

## Bearer
- **LoRa:** un piccolo riepilogo e metadati essenziali, secondo budget radio e payload effettivamente supportati.
- **BLE:** calibrazione/configurazione locale autorizzata; **Wi-Fi/Internet:** storico e grafici completi; **USB:** recupero di log e confronto con eventuale strumento di riferimento.
- **Trasporto fisico:** studente volontario che consegna un supporto o relay memorizzato senza disporre dell'audio originario.

## Esperimento software immediato
Generare finestre sintetiche di intensità con lunghi vuoti, drift, sensore staccato, stati di calibrazione diversi, orari incerti e ritardi di inoltro. I test devono verificare che non si confondano: media calcolabile, finestra mancante, sensore non calibrato, zero osservato e dati scaduti. Per il confronto con altre scuole, non sovrapporre automaticamente finestre diverse e mostrare la copertura dei campioni. Metriche software: perdita/ricostruzione delle finestre, anomalie rilevate, bytes, ritardo, errori di join. **Non trattare numeri sintetici come rilievi ambientali reali.**

## Prova fisica necessaria
Prima simulatore, poi due microfoni/sensori fissati in punti consentiti, almeno 4 schede LoRa, PC e se disponibile fonometro di riferimento adeguato. Annotare modello, alimentazione, posizione, schermatura del vento, calibrazione, incertezza e frequenza di campionamento. Se la catena non è calibrata si deve chiamare la quantità **indice/proxy acustico**, non livello certificato dB(A), LAeq o conformità normativa. Misurare TX/RX, finestra locale vs ricevuta, bytes, ritardi e autonomia sul banco; nessun risultato di copertura inventato.

## Privacy e sicurezza
**Nessuna registrazione persistente, trasmissione o ricostruzione delle voci.** Elaborazione locale di energia/aggregati soltanto; niente classificazione di persone, nessuna telecamera, niente postazioni in spazi privati. Autorizzazioni della scuola, informativa e valutazione del rischio per sensori acustici, log senza nomi; evitare granularità temporali inutilmente identificanti. Integrità, provenienza, sensori non fidati e valori anomali segnalati senza sostituzione tacita.

## Differenza rispetto al catalogo
UC-003 copre generici sensori rurali; UC-197 dati meteorologici, UC-223 prova ombra/sole, UC-228 bias di campionamento. **UC-242** è un protocollo didattico specifico di **osservazione acustica privacy-first**, con divieto di trattenere audio e distinzione fra indice non calibrato e misura riferibile a uno standard. Nessuna modifica PHY.

Riferimento concettuale di rete DTN: https://www.rfc-editor.org/rfc/rfc9171.html .
