# UC-338 — DNA: completare un kit di libri scolastici da più biblioteche offline

**Stato (24 novembre 2026):** proposta documentale, non implementata né testata. Difficoltà media-alta/alta. Nessuna modifica PHY LoRa congelato, MAC, driver o firmware.

## Problema concreto e attori
Un docente vuole predisporre un kit di testi riutilizzati per un gruppo didattico; i singoli volumi sono disponibili in biblioteche diverse, ma un elenco di offerte non dice se si possa completare l'intero kit, né se una copia sia già stata assegnata a un altro kit. Ad esempio, servono due volumi specifici di un manuale, un eserciziario obbligatorio e un testo facoltativo. Il titolo simile non basta, una variante richiede approvazione del docente e un codice digitale personale non si trasferisce automaticamente.

Attori: biblioteca scolastica A/B/C, docente che pubblica la lista esatta, referente assegnazioni, DNA/DNATrace per la spiegazione delle compatibilità (proposta di integrazione), nodi relay volontari e punto scolastico di ritiro. Scenario fittizio Milazzo–Venetico–Spadafora: le scuole condividono disponibilità di copie proprie da concedere in prestito o donare, senza denaro, contatti diretti fra minori o raccolta di bisogni economici personali. Le scuole reali richiedono accordo e autorizzazione.

## Perché PollicinoNet e bearer
Le liste, offerte e decisioni sono piccole, possono aspettare e attraversare partizioni. DISCOVERY annuncia categoria e disponibilità approssimativa; EXACT lega copia, edizione, componente e revisione della lista; SEMANTIC suggerisce alternative da revisionare, non sostituisce il requisito esatto. Il kit va costruito come problema di copertura di requisiti con capacità per singola copia, non come somma di match indipendenti.
- LoRa: digest lista, richieste compatte, disponibilità e stati, se il profilo attuale lo permette.
- BLE: scansione locale da companion e sincronizzazione breve.
- Wi-Fi/Internet: cataloghi autorizzati, metadati estesi e log; nessuna dipendenza dal cloud.
- Trasporto fisico: copie presso punti scolastici o USB per cataloghi; nessuna scansione o copia digitale non autorizzata del testo.

## Contratto e software immediato
`KitNeed={kit_alias,list_revision,required_slots[],optional_slots[],allowed_alternatives[],deadline,authority}`; `CopyOffer={copy_alias,edition_id,volume,format,components,condition_state,site_alias,inventory_epoch,availability,expiry}`; `Allocation={proposal_id,kit_alias,slot_id,copy_alias,inventory_epoch,owner_authority,decision,expiry}`. Distinguere DRAFT, PARTIAL, PROPOSED_COMPLETE, CONFIRMED_COMPLETE, PICKED_UP, EXPIRED, UNKNOWN. Una stessa copia soddisfa al massimo uno slot/kit (salvo esplicita regola di prestito non simultaneo fuori da questo pilot); coordinatore della copia decide in modo serializzato; durante partizioni solo proposte tentative, mai garanzia globale. Completezza confermata richiede decisioni valide di tutte le fonti e revisione della lista corrente; il ritiro è separato. Se l'autorizzazione può essere revocata, riconfermare prima del ritiro.
Simulare 3 biblioteche, 18 copie fittizie, 4 kit concorrenti con 3–4 requisiti ciascuno. Confrontare greedy per singolo titolo e assegnazione con vincoli (matching bipartito/ricerca esatta su piccolo dataset); provare volume errato, ISBN valido ma edizione sbagliata, componente assente, alternative non approvate, disponibilità scaduta, doppia assegnazione, revoca tardiva, replay, lista v2 e ritiro parziale. Misure: kit completi confermabili, slot mancanti, doppie assegnazioni (obiettivo zero), falsi completi (zero), numero di messaggi e latenza simulata. Non usare dati personali o inventari reali inizialmente.

## Hardware e privacy/sicurezza
4–6 schede e 2–3 PC o Raspberry, etichette per copie dimostrative, lettura barcode opzionale (ISBN reale soltanto per pubblicazioni autorizzate, alias copia distinto). Provare contatti disgiunti A→relay→B, poi ritorno delle conferme, senza pretendere atomicità del mondo fisico. Validare ritiro con inventario indipendente e ricevuta. Conservare solo pseudonimi di kit di laboratorio e inventario necessario; evitare di rendere pubblici nomi, classi, disponibilità economiche, itinerari, recapiti e codici digitali; autorizzazioni firmate, TTL, nessuna vendita o pagamento. Il personale può annullare un'assegnazione prima del ritiro.
## Originalità
UC-043 include già espressamente libri usati e match ISBN; non lo si ripropone. UC-194 tratta una singola prenotazione, UC-284 cicli di permuta, UC-266 equità per kit didattici, UC-315 idoneità del singolo strumento. Qui il nuovo invariante è **completezza di una distinta multi-componente esatta, con assegnazioni concorrenti e capacità per copia**. Il modulo può generalizzarsi a kit di componenti non critici, materiale scolastico e ricambi dimostrativi, senza trasformare PollicinoNet in marketplace centralizzato.

Riferimento: International ISBN Agency, https://www.isbn-international.org/content/isbn-assignment (edizioni, formati e volumi distinti); l'ISBN non attesta condizione, presenza di supplementi o trasferibilità di licenze.
