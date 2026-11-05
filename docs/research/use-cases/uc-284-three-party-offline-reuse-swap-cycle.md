# UC-284 — Scambio circolare di beni riutilizzabili fra più scuole disconnesse

**Data/stato:** 5 novembre 2026; proposta documentale, non implementata. Difficoltà **alta** per consenso, conflitti ed esecuzione fisica; PHY LoRa congelato, MAC, driver e firmware invariati.

## Problema e nuovo valore

Il normale marketplace offline (UC-043) mette in contatto una richiesta e un'offerta; la prenotazione di un singolo bene è già affrontata da UC-194. Ma tre persone possono avere offerte e bisogni **incrociati** senza che esista un abbinamento bilaterale: A possiede una calcolatrice e desidera un manuale; B possiede il manuale e desidera un hub USB; C possiede l'hub e desidera la calcolatrice. Nessuno scambio A↔B basta da solo. Occorre proporre un **ciclo di permuta 3-way**, raccogliere consenso indipendente e impedire di promettere la consegna se una sola persona non conferma.

Il pilot deve usare oggetti innocui, proprietà del laboratorio e identità sintetiche. **Non** gestisce denaro, pagamenti, crediti o garanzie di permuta atomica del mondo fisico.

## Attori, nodi e scenario messinese

Tre gruppi scolastici fittizi etichettati Rometta, Venetico e Messina (poi checkpoint veri autorizzati); proprietari degli oggetti, coordinatore/docente, nodo che propone il ciclo, cache/relay store-and-forward volontari e sede scolastica di consegna. Gli studenti non devono incontrare sconosciuti autonomamente: tutti gli scambi fisici passano da docenti e punti autorizzati.

**Perché PollicinoNet:** le richieste/offerte, i riferimenti di proposta, le conferme e gli aborti sono eventi piccoli e differibili. La ricerca del ciclo può avvenire su cache temporaneamente disconnesse; nessun proprietario deve essere online contemporaneamente agli altri.

## Bearer e contratti

- **LoRa:** soli handle di offerta/bisogno a vita breve, ID proposta, stato minimo `PROPOSED/CONFIRMED/ABORTED/EXPIRED` e digest (se fattibili sul bearer; mai elenco pubblico di necessità personali).
- **BLE:** sincronizzazione di richieste autorizzate e conferme ravvicinate.
- **Wi-Fi/LAN/Internet:** dettagli dei beni, condizioni e preferenze, grafo completo delle offerte, consensi autenticati.
- **USB/SD/trasporto fisico:** eventi di audit, documentazione, **beni reali consegnati** in un punto supervisionato.
- **DISCOVERY:** disponibilità di potenziale ciclo con handle opachi; **EXACT:** ID di oggetto, edizione/compatibilità, grafo proposto, epoch, scadenza, autorizzazioni e firme; **SEMANTIC:** categoria «calcolatrice/manuale/hub» non sostituisce la compatibilità esatta.

`SwapCycleProposal={proposal_id,offer_ids[],need_ids[],exact_compatibility_hashes[],owners[],deadline,epoch,terms_hash,reviewer_id}`. Le autorizzazioni private vanno al coordinatore, non ai relay.

## Sperimentazione solo software, eseguibile subito (non eseguita)

1. Generare 12 partecipanti e 18 articoli sintetici con compatibilità esatta; cercare cicli semplici di lunghezza **3–4**, senza ripetizione di persone/beni; limitare lo spazio di ricerca.
2. Simulare tre cache scollegate e inoltri LoRa virtuali; proporre un ciclo soltanto quando tutti gli archi sono verificati come compatibili da dati esatti.
3. Simulare conferme raccolte in ordine casuale; ritiro di un proprietario; scadenza; conferma duplicata; due cicli che competono per lo stesso bene; proposta vecchia dopo reboot; revoca a nodo isolato.
4. Non segnare `READY_FOR_SUPERVISED_HANDOFF` se manca **anche una sola conferma valida** legata alla medesima proposta/epoch. Se arriva un ritiro, bloccare nuovi handoff e marcare `ABORT_PENDING_CONVERGENCE`.
5. Distinguere `DIGITAL_READY` da `PHYSICAL_COMPLETED`: quest'ultimo richiede ricevute di consegna/ritiro verificate presso il docente, e gli effetti parziali sono espliciti; nessuna «atomicità fisica» deducibile dal protocollo.
6. Confrontare match solo bilaterali e cicli a 3–4 su **stessi dati sintetici**, riportando numero di cicli *proposti* e *completati* separatamente, conflitti/aborti, byte di controllo e tempi simulati. Non sostenere che i cicli migliorino l'esito in una comunità reale.

**Invarianti:** un bene non può essere `DIGITAL_READY` in due cicli attivi autorizzati dal proprietario; una conferma è valida solo per hash dei termini+epoch; nessuna consegna fisica è dichiarata senza ricevute indipendenti; un mancato consenso è `UNKNOWN`, non `YES`.

## Hardware e verifica fisica futura

Bastano **4–8 schede** e tre gruppi scolastici nello stesso istituto, isolati logicamente, con tre oggetti fittizi o beni scolastici innocui. I relay studenti portano capsule tra gruppi; un PC controlla proposte, firme e revoche; la chiusura avviene soltanto in una consegna supervisionata. Rilevare realmente eventi/byte e tempi di conferma, completezza delle ricevute, aborti e duplicati. Fase provinciale eventuale tra Messina, Villafranca, Rometta e Venetico senza utilizzare indirizzi o itinerari privati.

## Privacy e sicurezza

Dati sensibili come bisogni economici, preferenze e recapiti non vanno pubblicati via radio. Pseudonimi rotanti, consenso opt-in revocabile, condizioni esatte private, scadenze brevi, firme, anti-replay, limite anti-spam, rimozione delle offerte ritirate; vecchie copie nei relay non possono essere cancellate retroattivamente. Mai appuntamenti privati tra minori e sconosciuti, niente denaro né oggetti pericolosi o regolati. Prima distribuzione soltanto a scuola.

## Perché non è un duplicato

**UC-043** descrive il marketplace e il ciclo di vita *a coppie*; **UC-194** evita doppie prenotazioni di un singolo oggetto; **UC-015** riconcilia risorse; **UC-042** documenta passaggi fisici; **UC-059** riguarda competenze/servizi. **UC-284** studia l'invariante nuovo di **consenso congiunto e conflitto fra cicli multilateralmente dipendenti**; riusa i moduli esistenti e non crea un nuovo token di pagamento o servizio di scambio autonomo.
