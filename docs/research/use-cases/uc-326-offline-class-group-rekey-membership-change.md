# UC-326 — Gruppo didattico cifrato: uscita di un membro, nuova epoca e consegna differita

**Stato:** proposta documentale del 20 novembre 2026; nessuna implementazione o prova crittografica dichiarata. **Difficoltà:** alta. **Priorità:** alta per sicurezza, dopo la dimostrazione A→B→C.

## Problema concreto
Un gruppo di progetto di tre laboratori distribuisce appunti o documenti non pubblici. Un membro non è più autorizzato alla prossima versione, ma alcuni relay restano offline. Se le nuove capsule continuano a usare la vecchia chiave o un elenco membri obsoleto, un destinatario non autorizzato potrebbe leggere contenuti successivi alla rimozione. D'altra parte non possiamo cancellare da remoto contenuti già ricevuti e copiati quando l'accesso era valido.

Attori: responsabile/docente del gruppo, tre destinatari autorizzati, membro rimosso rappresentato da un **account sintetico**, registrar delle epoche, cache scolastiche e relay studenti che trasportano esclusivamente ciphertext o riferimenti. Nella prova i nomi delle località Messina, Milazzo e Venetico identificano partizioni logiche, non link reali.

## Perché PollicinoNet
Le transizioni di membership, i riferimenti alle chiavi di gruppo e le ricevute possono viaggiare in differita; il servizio EXACT può verificare contenuto cifrato/versione e stato policy prima della pubblicazione. La rete deve però dire chiaramente se un nodo offline conosce ancora solo l'epoca vecchia. **Non equivale a protezione retroattiva** e non esiste un istante globale di revoca garantito.

## Bearer
- **LoRa:** micro-avvisi firmati di epoch, hash del commit di membership, richieste di aggiornamento o stato UNKNOWN; niente segreti di gruppo in chiaro.
- **BLE:** consegna autenticata di piccoli oggetti di controllo in prossimità, quando disponibile.
- **Wi-Fi/LAN/Internet:** aggiornamenti crittografici completi, contenuti cifrati e verifiche del registrar.
- **USB/SSD/trasporto fisico:** trasferimento cifrato di un pacchetto didattico più grande.
Non modificare il PHY LoRa e non assumere che un modello di sicurezza MLS funzioni automaticamente con trasporti arbitrariamente differiti.

## Macchina a stati proposta
GroupEpoch = {group_id_pseudonymous, epoch, membership_commit_hash, policy_revision, trusted_issuer, valid_from_context, previous_epoch_ref, recipients_commitment, content_key_context}.
Stati: CURRENT, STALE, CONFLICTED_EPOCH, NEEDS_RESYNC, ACCESS_DENIED, ACCEPTED. Una nuova pubblicazione privata richiede una nuova epoca autorizzata, verifica del destinatario e cifratura per il solo gruppo corrente. I relay non devono avere chiavi per decifrare.

**Nota di sicurezza:** quando commit di membership arrivano fuori ordine, bisogna disporre di una storia verificabile o di una decisione autorevole prima di produrre una nuova pubblicazione. Due aggiornamenti contemporanei non devono generare due gruppi che si ritengono entrambi autoritativi. La rimozione del membro deve impedire l'accesso a **nuovi** dati protetti dopo una transizione validata, non cancellare il passato già visto.

## Test software immediato (non eseguito)
Simulare cinque nodi e 18 documenti fittizi, epoche e0–e3. Inviare un avviso di rimozione prima e dopo i documenti, variare ordine dei commit, riavvii, cache stale, credenziale rimossa, nodo che non riceve il rekey e revoca ricevuta tardi.
- Nessuna nuova busta deve essere cifrata per il gruppo e0 dopo approvazione della sua sostituzione.
- Un destinatario disconnesso privo di materiale di epoca corrente vede NEEDS_RESYNC, non un contenuto pubblicato in chiaro.
- Un membro rimosso non riceve nuove chiavi autorizzate dall'applicazione; i documenti già posseduti restano una limitazione esplicita.
- I controlli devono basarsi su veri test di autorizzazione/decifratura con dati fittizi, non sulla semplice presenza di un tag nei metadati.
- Conflitti di commit devono restare CONFLICTED_EPOCH sino a riconciliazione attendibile.

## Hardware successivo e metriche
Due PC, un registrar isolato e quattro relay LoRa, con tre partizioni temporali. Provare la propagazione degli avvisi compatti e il recupero di pacchetti cifrati via bearer ricco, **disabilitando collegamenti di rete imprevisti** nel braccio LoRa; registrare epoca, rifiuti, messaggi accettati e ritardi fisici reali solo quando misurati. Niente dati veri degli studenti. Nella fase di rete provinciale, relay volontari store-and-forward e checkpoint autorizzati, mai cronologia degli spostamenti.

## Sicurezza, privacy e anti-duplicazione
Elenco dei membri protetto e pseudonimizzato, chiavi conservate solo negli endpoint autorizzati, log minimizzati e TTL. Revoca tardiva, compromissione endpoint e copie anteriori sono limiti non eliminabili con sola propagazione LoRa. UC-019 tratta fiducia/revoca in generale; UC-023 il mailbox privato; UC-077 la cancellazione differita; UC-170 la migrazione di algoritmi. Qui la novità è **il cambio effettivo della chiave di accesso del gruppo e il blocco del contenuto nuovo durante partizioni**.

**Riferimento:** RFC 9420 (Messaging Layer Security) per gruppi/epoche/commit e limitazioni dei membri offline, https://www.rfc-editor.org/rfc/rfc9420.html . È un riferimento concettuale, NON una dichiarazione di implementazione MLS in PollicinoNet.
