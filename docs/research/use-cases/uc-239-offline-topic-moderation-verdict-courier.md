# UC-239 — Moderazione differita dei messaggi delle stanze offline

Stato: proposta 21 ottobre 2026, non implementata.

## Problema e attori
Una stanza di un laboratorio scolastico riceve un contributo mentre il moderatore è disconnesso. Il trasporto dell'oggetto non deve significare pubblicazione automatica; approvazioni e ritiri possono giungere in ordine diverso a due cache. Attori: autore dimostrativo, moderatore autorizzato, due cache/lettori e relay studenti fra checkpoint Messina e Venetico. Solo post sintetici per il primo esperimento.

## Perché PollicinoNet e bearer
LoRa diffonde identificativi, hash, richieste di revisione, approvazioni o ritiri firmati. BLE riconcilia le decisioni durante incontri; Wi-Fi trasferisce i post completi; Internet non è necessario; un laptop può portare copie fisiche fra laboratori. Decisioni legate a post_id, content_hash, room_id, policy_epoch, decision_id, moderator_role e supersedes.

## Software immediato
Due cache isolate e un moderatore virtuale. Stati SUBMITTED, PENDING_REVIEW, APPROVED, REJECTED, WITHDRAWN, POLICY_UNKNOWN. Un post può viaggiare come PENDING_REVIEW, ma non essere visibile prima dell'APPROVED valido. Iniettare verdetto prima del post, ritiro successivo, doppia approvazione, moderatori in conflitto, firma/ruolo errati, epoch superata, orologio incerto e riavvio. Verificare che una decisione vecchia non annulli il ritiro più recente secondo la policy, e che stati ambigui non siano esposti come autorizzati. Metriche: esposizioni indebite (obiettivo zero nel test), cache stale, convergenza e bytes trasportati.

## Prova fisica
Tre PC (due cache e un moderatore), 4–6 schede LoRa, messaggi fittizi. Annotare ricezione del post, ricezione del verdetto, visibilità effettiva e ritiro; confrontare eventi nei due checkpoint.

## Privacy e sicurezza
Niente contenuti di minori o casi reali di abuso nella demo. Autorizzazioni di ruolo, firme, protezione anti-replay, minimizzazione dei log e validità limitata. Un ritiro diffuso non può garantire cancellazione da copie già esportate o nodi mai più raggiunti. Difficoltà alta, non è moderazione istantanea.

## Novità rispetto ai casi presenti
UC-083 consegna notifiche, UC-236 seleziona topic e zona, UC-077 propaga tombstone e UC-132 aggiorna bollettini ufficiali. UC-239 distingue espressamente **quarantena di contenuti di comunità, revisione, autorizzazione editoriale e ritiro** in presenza di partizioni. Non richiede interventi al PHY LoRa.

Riferimento: https://www.rfc-editor.org/rfc/rfc9171.html .
