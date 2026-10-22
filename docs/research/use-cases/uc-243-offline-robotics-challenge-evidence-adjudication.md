# UC-243 — Torneo didattico di robotica con prove e punteggi differiti

**Stato:** proposta documentale del 22 ottobre 2026; non implementata né testata su robot. **Difficoltà:** medio-alta.

## Problema e storia d'uso
Due laboratori partecipano a una sfida di robotica a tappe. Una squadra annuncia di aver completato un percorso, ma il risultato arriva prima delle prove oppure una verifica successiva modifica il punteggio. Una rete intermittente non può trattare il primo messaggio ricevuto come classifica definitiva.

**Scenario Messina:** Romeo esegue una sfida su un tracciato chiuso e supervisionato in laboratorio; un altro gruppo di studenti presso un secondo checkpoint scolastico riceve risultati e verbali in momenti diversi. Nessun robot percorre strade o spazi pubblici in autonomia.

## Attori e perché PollicinoNet
Robot Romeo o simulatore, team di studenti, arbitro locale, revisore remoto, due cache/scoreboard e 4–6 relay. PollicinoNet conserva identificativi, hash e aggiornamenti durante le partizioni, permettendo una **classifica provvisoria verificabile** e successiva riconciliazione. Ogni tentativo produce challenge_id, attempt_id, rules_hash, robot_profile, claim, evidence_hash, local_referee_signature, revision e verdict_state.

## Bearer
- **LoRa:** piccoli annunci di tentativo, punteggio provvisorio, digest delle prove e verdetti.
- **BLE/Wi-Fi:** recupero dei log del robot e delle prove digitali quando disponibile; **Internet:** archivio o streaming non necessari; **USB/memoria fisica:** eventuale trasferimento di prove più grandi.
- Non si trasmettono video tramite LoRa: dimensioni e privacy lo renderebbero inappropriato.

## Esperimento software immediato
Due simulatori di robot, arbitro e scoreboard disconnessi. Iniettare: tentativo duplicato, video mancante, hash non coerente, un punteggio corretto dopo la prima pubblicazione, regole di gara con versione differente, due arbitri in disaccordo, messaggio di approvazione prima del claim e perdita di rete durante la riconciliazione. Stati proposti: SUBMITTED → EVIDENCE_PENDING → PROVISIONAL → REVIEWED/REJECTED/CONTESTED. **Un risultato PROVISIONAL non diventa VERIFIED solo perché è stato consegnato.** Criteri di accettazione: versioni legate a rules_hash; contestazioni conservate; nessun doppio conteggio dello stesso attempt_id; punteggio definitivo soltanto dopo revisione autorizzata. Prodotto FSL: scoreboard locale, importatore di prove e suite pytest di test di accettazione.

## Prova hardware necessaria
Romeo su percorso da banco a velocità bassa, arresto locale funzionante e supervisione; due PC, 4–6 schede e eventualmente due camere puntate **solo sul tracciato**. Confrontare prove del robot, osservazione indipendente e timestamp con incertezza; misurare ritardo dei verdetti, bytes per bearer e incongruenze. Prima di aggiungere tappe o droni valutare sicurezza meccanica, norme applicabili e supervisione adeguata.

## Privacy e sicurezza
Video facoltativo senza volti, firme per arbitri, log minimi, nessuna pubblicazione di graduatorie nominative o monitoraggio degli spostamenti. Contestazioni gestite da docente e senza sanzioni automatiche. La firma dimostra l'origine del referto, **non la verità fisica della prestazione**; servono riscontri indipendenti. Nessun impiego del robot in missioni critiche e nessun comando motorio remoto non supervisionato.

## Differenza rispetto al catalogo
UC-010 tratta missioni differite, UC-215 dimostra il trasferimento dati tramite Romeo, UC-235 giochi di enigmi tra scuole e UC-237 conformità del software a specifiche. **UC-243** valuta invece una **prestazione fisica**, distinguendo risultato dichiarato, prova, revisione e classifica durante partizioni. Nessuna modifica del PHY LoRa.

Riferimento di contesto: https://www.rfc-editor.org/rfc/rfc9171.html .
