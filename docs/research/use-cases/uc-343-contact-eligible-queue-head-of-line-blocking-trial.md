# UC-343 — Relay scolastico: non perdere un incontro per il primo messaggio in coda

**Stato (26 novembre 2026):** proposta documentale, non implementata né testata. Difficoltà media. PHY LoRa congelato, MAC, driver e firmware invariati.

## Problema e attori
Un relay contiene tre messaggi piccoli, tutti con uguale priorità: uno per il checkpoint A e due per B. Incontra B, ma il primo elemento della coda è per A. Un FIFO rigido può lasciare inutilizzato l'incontro; scavalcare senza regole può invece violare autorizzazioni, dipendenze o affamare A. Docente, relay volontari, checkpoint A/B, destinatari applicativi e collector indipendente.

Scenario ipotetico: A=Venetico, B=Milazzo; relay inizialmente in laboratorio, poi eventualmente trasportati durante spostamenti ordinari. Nessuna copertura o presenza personale presupposta.

## Perché PollicinoNet e bearer
Il relay conserva gli oggetti non consegnabili e seleziona quelli effettivamente eleggibili durante un contatto autenticato. DISCOVERY: capability o handle di destinazione opaco e autorizzato; EXACT: oggetto, policy, dipendenze e ricevuta; SEMANTIC: motivazione di rinvio, non prova di raggiungibilità.
- LoRa: piccoli messaggi e controllo entro limiti già disponibili; BLE: scambio ravvicinato; Wi-Fi/Internet: log, oggetti più grandi o percorso alternativo esplicito; USB/trasporto fisico: coda e log trasferiti tra postazioni, distinti dalla consegna radio.
- Riferimento concettuale: RFC 9000 §2 (https://www.rfc-editor.org/rfc/rfc9000.html#section-2), flussi indipendenti; non si propone QUIC su LoRa.

## Contratto e politica
QueueItem={item_id, destination_scope, eligible_peer_policy, dependencies[], size, priority, admitted_at, expiry, custody_state}; Contact={session_id, authenticated_peer_scope, bearer, policy_epoch, observed_window}; Decision={item_id, session_id, decision, reason, policy_version}; Receipt={item_id, destination_scope, acceptance_id, auth}.
Confrontare FIFO rigido e selezione FIFO fra soli elementi eleggibili con scansione limitata (oppure sottocode per scope). Non inviare a B un oggetto destinato ad A se B non è relay autorizzato per quell'oggetto. Un oggetto dipendente aspetta il proprio prerequisito; nessuna falsa conferma di consegna da un relay intermedio. Conservare scadenze, quote e progressi verificati; alternare scope eleggibili per evitare starvation, senza promettere servizio a scope irraggiungibili.

## Software subito (piano)
Python: 5 nodi virtuali, 24 capsule, 12 finestre di contatto deterministiche; stessi input e budget per entrambe le politiche. Fixture minima: A1, B1, B2 in coda; contatto B poi A, con B non autorizzato a custodire A1. Aggiungere dipendenza B3→B2, policy revocata, riavvio, ricezione duplicata, TTL, contatto insufficiente e caso in cui entrambi gli scope sono eleggibili.
Misurare consegne applicative uniche entro finestra, opportunità inutilizzate per blocco della testa, attesa per scope, scansioni e residuo per scadenza. Gate: nessuna consegna non autorizzata o fuori dipendenza, nessuna perdita silenziosa della coda, B1/B2 selezionabili in un contatto con capacità sufficiente senza rimuovere A1. Un mancato contatto con A non è starvation imputabile allo scheduler.

## Hardware e sicurezza
4–5 schede e 2 PC; stesso workload e profilo radio già approvato, contatti applicativamente abilitati a finestre separate, log indipendenti, budget radio rispettato. Confronto appaiato, ordine alternato, contare tentativi e accettazioni reali; distinguere controllo con trasporto fisico da radio. Nessun GPS, nome studente o elenco pubblico dei destinatari; pseudonimi di campagna, limiti su scansioni/annunci, autorizzazione dei peer, log con accesso limitato. Nessuna prova su strada o contatto operativo.

## Distinzione
UC-045 ordina il prelievo da una fonte, UC-095 gestisce equità e budget, UC-108 pressione di coda, UC-159 preemption di trasferimento in corso, UC-304 contatti simultanei. UC-343 isola il blocco della testa causato da destinazione non eleggibile, anche con oggetti piccoli, uguale priorità e un solo peer alla volta; estende queste politiche senza duplicarne lo scopo.
