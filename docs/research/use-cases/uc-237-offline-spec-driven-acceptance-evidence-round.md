# UC-237 — Accettazione SDD con evidenze fra laboratori disconnessi

Stato: proposta 21 ottobre 2026, non implementata.

## Problema e attori
Una classe FSL sviluppa una funzione con un coding agent e un tutor deve accertare quali requisiti siano soddisfatti. Test verdi riferiti a una vecchia specifica non equivalgono ad accettazione. Coinvolge committente/docente, gruppo sviluppatore, revisore, worker CI e relay studenti tra laboratori di Messina e Venetico.

## Perché PollicinoNet; bearer
Piccoli contratti e ricevute si scambiano anche con assenza di percorso end-to-end. LoRa: spec_id, revision, hash e stato della revisione. BLE: manifest e report brevi. Wi-Fi: repository, log e prove. Internet: CI e forge opzionali. Trasporto fisico: Git bundle su laptop/USB. Tutti i risultati sono legati a hash esatti, non a etichette semantiche.

## Contratto e test software
SpecPack: spec_hash, requirement_ids, examples, reviewer_role, expiry. Evidence: spec_hash, commit_hash, test_suite_hash, environment_hash, requirement_id, outcome, log_hash. Stati: DRAFT, SPEC_APPROVED, EVIDENCE_PENDING, REVIEW_REQUIRED, ACCEPTED, REJECTED, UNKNOWN.
Due laboratori simulati scambiano un progetto Python con tre criteri Given/When/Then. Iniettare: spec v2 che arriva prima di test v1, tutti i test verdi ma copertura incompleta, esito duplicato, commit errato, revisore non autorizzato, artefatto mancante e ritardi. Il gate resta UNKNOWN finché hash, prove e approvazione umana non coincidono. Metriche: falsi ACCEPTED (obiettivo zero), requisiti coperti, ritardi di verifica e byte trasferiti.

## Prova fisica
Due PC e 4–6 schede fra aule scolastiche isolate, con docente revisore. Inviare digest LoRa e Git bundle via Wi-Fi durante contatti reali. Registrare tempi, invii, ricevute e test effettivamente eseguiti.

## Sicurezza; difficoltà
Solo codice fittizio/pubblico, runner isolati, niente segreti GitHub, no valutazione automatica degli studenti, firme del reviewer e permessi di esecuzione espliciti. Un test PASS non è garanzia generale di correttezza. Difficoltà medio-alta.

## Originalità
UC-081 è CI distribuita, UC-054 è consegna di compiti, UC-221 è ricevuta applicativa. UC-237 introduce tracciabilità requisito → test → commit → evidenza → approvazione umana, utile all'AI-Assisted Software Engineering. Nessun cambiamento PHY.

Riferimento: https://git-scm.com/docs/git-bundle .
