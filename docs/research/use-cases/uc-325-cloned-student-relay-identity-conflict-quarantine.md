# UC-325 — Identità di relay duplicate dopo il ripristino di una scheda: rilevazione prudente e quarantena

**Stato:** proposta documentale del 20 novembre 2026. Nessun test implementato, nessuna osservazione fisica. **Priorità:** alta per la rete didattica. **Difficoltà:** medio-alta in software, alta su hardware/trust.

## Problema concreto e attori
In laboratorio si ripristina per errore un'immagine di configurazione destinata a una scheda su due relay fisicamente diversi. Possono comparire lo stesso ID logico, il medesimo contatore o materiale di enrollment riutilizzato. Se due nodi si presentano come un unico relay, il collector potrebbe attribuire code, ricevute e autorizzazioni alla scheda sbagliata. Ci sono docente responsabile, due schede, registrar scolastico, collector, tre altri relay volontari e destinatario applicativo.

Scenario: una scheda prestata a uno studente di Rometta e un relay conservato in laboratorio a Milazzo producono affermazioni apparentemente attribuite allo stesso dispositivo. La rete NON deve identificare né accusare uno studente dalla sola anomalia. La localizzazione degli studenti non viene registrata.

## Perché PollicinoNet e bearer
Le osservazioni arrivano attraverso percorsi e tempi differenti: store-and-forward conserva sia gli eventi sia la loro incertezza; può trasportare una segnalazione compatta a un registrar prima di avere collegamento Internet.
- **LoRa:** solo riferimenti/avvisi di conflitto compatti previsti dall'adapter esistente, fingerprint ridotti con ambiguità esplicita e richieste di verifica; non inviare chiavi segrete.
- **BLE/QR/USB:** controllo di prossimità in laboratorio e acquisizione diagnostica supervisionata.
- **Wi-Fi/LAN/Internet:** prove complete, log e intervento del registrar.
- **SSD o trasporto fisico:** fascicolo cifrato e autorizzato di diagnostica, non dati personali.

DISCOVERY serve a individuare un possibile conflitto, EXACT verifica identità e autorizzazione; SEMANTIC non prova il possesso di una specifica scheda. Nessun cambiamento a PHY LoRa congelato, MAC o firmware in questo documento.

## Modello dati e stati proposti
IdentityConflict = {campaign_id, claimed_node_id, credential_fingerprint, enrollment_epoch, boot_epoch_if_available, signed_event_id, claim_source, observation_interval, clock_uncertainty, evidence_hash, registrar_decision}.
Stati separati: NORMAL, SUSPECTED_CONFLICT, PENDING_PHYSICAL_CHECK, QUARANTINED, REENROLLED, INCONCLUSIVE. Il sospetto non revoca automaticamente un altro relay innocente; policy e decisione dell'autorità devono essere esplicite. Non supporre un ID hardware affidabile o una secure element se non presenti.

**Limite fondamentale:** se due dispositivi possiedono davvero la *stessa chiave privata*, una firma valida da sola NON permette di distinguere i due oggetti fisici. Contatori divergenti, nonces e cronologie possono generare un indizio di conflitto, non una prova completa di clonazione o un'identificazione della persona.

## Prova immediata solo software (proposta, non eseguita)
Sei nodi simulati, 30 capsule e tre condizioni: (A) due ID uguali ma chiavi diverse, (B) due istanze di dispositivo con la stessa credenziale sintetica, (C) riavvio innocuo dello stesso nodo con contatori ripartiti. Inserire eventi duplicati, ritardi, cronologie intercalate, scadenze, collector parzialmente scollegati, consenso alla verifica mancante.
- Misurare falsi allarmi e conflitti non rilevati nei fixture *etichettati*, senza attribuire accuratezza generalizzabile al mondo reale.
- Un ID uguale con chiavi diverse non deve fondere inventari o ricevute; una credenziale condivisa non deve generare falsa certezza sul dispositivo fisico.
- Quarantena di abilitazioni sensibili quando il registrar dispone di prove sufficienti, e stato INCONCLUSIVE se mancano log.
- Conservare i messaggi già custoditi per riconciliazione autorizzata, senza dichiarare completata la consegna.

## Hardware richiesto, poi
Due schede in laboratorio configurate con **identificativi di prova sintetici** (mai clonare credenziali reali), altre due schede relay e due PC. Confrontare letture di due dispositivi fisici, evidenze applicative e ripristino tramite re-enrollment distinto, misurando i contatti con log indipendenti. Solo dopo valutare due checkpoint autorizzati a Rometta e Milazzo. Nessuna presunzione su RF fra comuni.

## Privacy, sicurezza, criteri di accettazione
Nessun nome, itinerario o attribuzione di colpa nei payload. Anomalie revisionate dal docente; prove cifrate con minimizzazione e scadenza; vietato trasmettere segreti o dettagli di provisioning via LoRa. Richiedere approvazione fisica per re-enrollment e rotazione delle credenziali coinvolte. Esito PASS del simulatore solo se le collisioni non fondono dati, la quarantena non è motivata da una sola osservazione debole e le prove mancanti restano INCONCLUSIVE. Non promettere rilevazione universale della clonazione.

**Differenze dai casi esistenti:** UC-068 cura l'enrollment iniziale, UC-274 collisioni di hint brevi, UC-064 storie firmate divergenti, UC-307 perdita del nodo, UC-322 cambio di custode. Qui si testa **l'ambiguità tra due istanze fisiche che si presentano con la stessa identità** dopo un errore di immagine/ripristino, senza scambiare l'identità crittografica per prova di unicità dell'hardware.

## Riferimento tecnico
NIST SP 800-63B-4 (2025), gestione dei rischi delle credenziali sincronizzabili e della prova di possesso: https://pages.nist.gov/800-63-4/sp800-63b.html
