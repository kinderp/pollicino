# UC-336 — Raiatea / Romeo: dagli schemi elettrici alla connettività verificata

**Stato:** proposta documentale del 23 novembre 2026; nessun parser, modello AI o test elettrico eseguito. **Priorità:** alta per Raiatea, DNA e robotica educativa. **Difficoltà:** medio-alta software, alta per revisione e prove elettriche.

## Problema in parole semplici
Nel disegno di un circuito due linee possono incrociarsi senza essere elettricamente collegate; un minuscolo punto o un'etichetta possono cambiare tutto. Se un modello AI descrive un'immagine dello schema di Romeo, potrebbe **inventare collegamenti o approvare un circuito non sicuro**. Serve conservare il file KiCad esatto, la netlist nativa, l'esito del controllo elettrico (ERC), le osservazioni AI *provvisorie* e la revisione umana, distinguendo errori da mancanza di evidenze.

## Attori e scenario messinese
Laboratorio con schemi didattici fittizi a Milazzo, laboratorio revisore a Rometta o Venetico, docente elettronica, archivio Raiatea, motore DNA per individuare requisiti mancanti, 3–4 relay LoRa degli studenti volontari, due PC. Primo esercizio solo su un circuito LED/resistenza con alimentazione a bassissima tensione e limitazione di corrente, senza motori, azionamenti reali, batterie da caricare o circuiti di potenza. Le scuole e i collegamenti sono esempi, non deployment.

## Perché PollicinoNet e bearer
Un aggiornamento di schema potrebbe arrivare dopo un vecchio rapporto che lo dichiarava corretto: store-and-forward e versioni servono a invalidare revisioni obsolete. **LoRa (PHY congelato):** hash e ID di progetto, stato, richieste piccole e ricevute applicative; mai immagini pesanti. **BLE:** controllo vicino al checkpoint se disponibile. **Wi-Fi/LAN/Internet:** schema KiCad, netlist, report ERC, immagini e documentazione autorizzata. **USB/SSD, stampa e trasporto fisico:** materiali più grandi e circuito dimostrativo con ricevute di custodia separata.

## Oggetto dati consigliato
project_id; schematic_source_hash; revision_id; native_netlist_hash; kicad_version; erc_rules_version; erc_report_hash; extracted_graph_hash; discrepancy_ids; crossing_or_junction_review; polarity_review; ai_hypothesis_status; human_review_signature; license; release_state=DRAFT|ERC_REPORTED|HUMAN_REVIEWED|REJECTED|UNKNOWN; dependent_romeo_demo_task_id_optional. Qualsiasi cambio di schema invalida lo stato approvato delle spiegazioni e dei report legati alla revisione precedente.

## Workflow
RECEIVED_UNVERIFIED → PARSED_NATIVE → ERC_REPORTED → DIFFERENCES_REVIEWED → HUMAN_APPROVED_DEMO, oppure REJECTED/UNKNOWN. La connettività attesa deriva da netlist generata **dal file sorgente**, non da pixel interpretati da AI. L'ERC verifica determinate regole ma **non certifica la sicurezza elettrica**. DNA può segnalare parti mancanti o requisiti; solo il docente autorizza un'eventuale dimostrazione pratica.

## Software subito — soltanto specificato
Progettare 3 schemi sintetici KiCad: incrocio senza connessione, giunzione esplicita, etichetta errata. Produrre in ambiente controllato netlist di riferimento e report ERC; simulare 6 revisioni tardive, 3 mismatch di hash, 2 proposte AI discordanti e 2 approvazioni obsolete. Il validatore Python deve confrontare grafo/connettività con la netlist nativa, mantenere differenza errori vs warning, distinguere UNKNOWN quando manca la fonte e richiedere nuovamente revisione dopo una modifica. Niente esecuzione automatica di macro, comandi o firmware presenti nei file o suggeriti da testi di terzi. I test non sono stati realizzati né eseguiti.

## Hardware reale — successivamente
3–4 schede LoRa, 2 PC con KiCad offline, eventuale breadboard con alimentatore a bassissima tensione protetto e limitato in corrente, con supervisione. Provare A→B→C in due contatti separati, riservando LoRa solo agli stati compatti. Se si vuole assemblare il piccolo circuito, verificare indipendentemente cablaggio e assorbimento; **non connettere o pilotare autonomamente il robot Romeo**. Nessuna misura o validazione elettrica dichiarata.

## Privacy, sicurezza e criteri
Solo schemi e immagini autorizzati e con licenza, nessuna password, schema di impianti reali, dati nominativi o itinerari di studenti. Verifica crittografica di hash/stati e accessi per ruolo; i documenti sono dati, mai istruzioni per strumenti. **PASS software** solo se topologie mutate invalidano revisioni e l'AI non diventa fonte normativa; **FAIL** se ERC o AI approvano da soli un circuito; **UNKNOWN** se manca netlist o revisione. PHY LoRa, MAC, driver e firmware invariati.

## Anti-duplicazione
UC-010 parla di mailbox robot, UC-099 di pipeline documentali Raiatea, UC-120 di invalidazione generale di derivati, UC-261 di approvazione di missioni AI, UC-293 di ricambi e UC-333 di pezzi stampati. **UC-336 riguarda specificamente l'ambiguità fra immagine dello schema, connettività elettrica nativa, report ERC e revisione umana su versioni che arrivano fuori ordine.**

## Fonti
KiCad Schematic Editor e regole ERC (connessioni, incroci, limiti della verifica automatica): https://docs.kicad.org/10.0/en/eeschema/eeschema.html

KiCad 9.0 electrical rules checking: https://docs.kicad.org/9.0/en/eeschema/eeschema.html
