# UC-344 — DNA: riparare un bene usando componenti recuperati da un altro

**Stato (26 novembre 2026):** proposta documentale, non implementata/testata. Difficoltà medio-alta (prototipo software medio). PHY LoRa congelato e altri livelli radio invariati.

## Problema e attori
Un laboratorio ha un supporto didattico danneggiato; un altro possiede un oggetto donatore da cui si potrebbe recuperare una clip o una rotella. Il catalogo non deve promettere contemporaneamente l'oggetto intero e le parti che verrebbero rimosse. Occorre decidere fra riuso integrale, riparazione e recupero di parti; la separazione fisica è un evento irreversibile, non una semplice prenotazione. Docenti/custodi proprietari, laboratori maker, DNA per match e spiegazioni, relay, revisore e punto di ritiro supervisionato.
Esempio ipotetico Milazzo–Spadafora–Venetico: supporti plastici dimostrativi e parti meccaniche innocue, di proprietà scolastica, non apparecchi elettrici o rifiuti. Nessun pagamento e nessuna iniziativa di contatto fra minori e sconosciuti.

## Perché PollicinoNet e bearer
Domande, offerte e decisioni viaggiano in differita anche senza un server disponibile. DNA rappresenta un grafo di possibilità alternative, non afferma che una parte esista finché non verificata; DNATrace può documentare provenienza non personale della parte, se integrato.
- DISCOVERY: categoria del bisogno e handle temporaneo del donatore; EXACT: inventario, revisione, autorizzazione, stato fisico e evidenze; SEMANTIC: suggerimento di compatibilità, non accettazione.
- LoRa: richieste e stati compatti se supportati; BLE: verifica locale; Wi-Fi/Internet/USB: foto senza persone, CAD, schede e log; trasporto fisico: bene/parti fra punti autorizzati. Non si confonde la consegna del record con quella del bene.

## Contratto e regole
Donor={asset_alias, owner_authority, inventory_epoch, condition, whole_reuse_state, candidate_parts[], parent_child_constraints}; Plan={plan_id, donor_alias, inventory_epoch, action, mutually_exclusive_claims[], destination_need, approvals, expiry}; PhysicalEvent={event_id, plan_id, part_alias, source_asset, inspection, status, reviewer, evidence_hash}.
Stati: CANDIDATE → RESERVED_BY_OWNER → AUTHORIZED → REMOVED_UNVERIFIED → INSPECTED/REJECTED → HANDED_OVER. Il proprietario è autorità unica per ciascun bene; offline gli altri possono proporre, non confermare. Se il bene è promesso intero non autorizzare estrazioni incompatibili. Dopo rimozione confermata, annullare l'offerta intera della vecchia revisione e creare nuove parti soltanto dopo ispezione. Una scadenza non annulla un evento fisico; revisione e riconciliazione umana se manca una ricevuta. Nessun algoritmo decide automaticamente la distruzione di un bene.

## Software subito (piano)
12 donatori sintetici, 20 bisogni, 4 laboratori virtuali; grafo con conflitti fra intero/parti e fra operazioni incompatibili. Confrontare matching indipendente e piano vincolato (backtracking piccolo o solver), senza automatizzare la scelta umana. Simulare richieste concorrenti, doppia promessa, revisione stale, disassemblaggio parziale, parte mancante, crash, scadenza, autorizzazione revocata.
Gate: zero doppie assegnazioni incompatibili confermate; nessuna parte disponibile prima dell'ispezione; nessun ritorno automatico a intero dopo separazione; ogni proposta spiega risorse consumate, alternative e autorità. Misurare bisogni soddisfacibili, conflitti evitati, richieste pendenti, beni conservati interi; non dichiarare risparmio ambientale reale.

## Hardware, privacy e difficoltà
4–6 schede, due PC, oggetti dimostrativi a incastro e contenitori con etichette fittizie; prova supervisionata di inventario, separazione innocua e consegna. Escludere batterie, schede alimentate, apparecchi di rete elettrica, materiali pericolosi, smontaggio di rifiuti o parti strutturali. Non pubblicare seriali, foto personali o dati economici. Firma delle transizioni, controllo proprietario, audit limitato e autorizzazione esplicita al trasporto. Se esteso a RAEE reali, occorrono verifica normativa e soggetti autorizzati, fuori ambito del prototipo.

## Distinzione
UC-043 tratta riuso in generale; UC-284 scambi circolari; UC-293 verifica compatibilità; UC-338 assegna copie già esistenti a kit; UC-113 segue ticket di manutenzione. Qui la decisione cambia fisicamente l'inventario: il bene intero e le parti candidate sono alternative incompatibili, e la parte passa da potenziale a verificata solo dopo un evento fisico. Non è un nuovo marketplace separato.
