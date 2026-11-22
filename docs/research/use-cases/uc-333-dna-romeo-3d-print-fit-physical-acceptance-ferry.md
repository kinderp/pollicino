# UC-333 — DNA / Romeo: un ricambio dimostrativo stampato non è automaticamente compatibile

**Stato:** proposta documentale del 22 novembre 2026, nessun prototipo o test eseguito. **Priorità:** alta per fablab e robotica scolastica. **Difficoltà:** media software, medio-alta su misure reali.

## Problema in parole semplici
Un laboratorio richiede una **piccola clip non strutturale di prova** per un mock-up del robot Romeo. Un'altra scuola stampa l'oggetto, ma «stampa completata» non significa «si incastra davvero». Una differenza fra dimensioni CAD, orientamento, materiale, macchina e pezzo reale può rendere il componente inutilizzabile. DNA dovrebbe descrivere il bisogno e verificare i requisiti del pezzo; PollicinoNet deve portare file e risultati fino a una decisione umana. **Non si autorizza il montaggio di ricambi safety-critical** o parti che possano compromettere movimento, alimentazione, isolamento elettrico o stabilità.

Per le tolleranze di stampa e le dipendenze da orientamento, geometria e materiale vedere il produttore Prusa: https://help.prusa3d.com/article/modeling-with-3d-printing-in-mind_164135 .

## Attori e rete messinese
Laboratorio richiedente con un *supporto di prova* inerte, referente DNA, fablab scolastico con stampante 3D, operatore docente, revisore con calibro, 3–4 relay volontari degli studenti e 2 checkpoint simulati a Milazzo/Rometta/Venetico. Il pezzo fisico può essere trasportato fra sedi; i dati arrivano anche dopo via store-and-forward. Le località non implicano link LoRa misurati.

## Perché PollicinoNet
La richiesta contiene un piccolo elenco di quote critiche e un digest della versione; gli STL/3MF e report completi si spostano su bearer più veloci. Una misura fatta dopo la consegna può essere diffusa come revisione tardiva senza cambiare la geometria originale. DNA confronta dimensioni e limiti richiesti; un docente decide se il pezzo dimostrativo supera la prova per **quella configurazione**.

## Bearer
- **LoRa:** richiesta/annuncio per hash di geometria, stato di revisione, report-id, piccola ricevuta.
- **BLE:** verifica locale e associazione al pezzo tramite QR o ID, senza tracciamento di persone.
- **Wi-Fi/LAN/Internet:** CAD/STL/3MF, profili di stampa, foto del pezzo e misure; Internet opzionale.
- **USB/SSD e trasporto fisico:** file e oggetto stampato vero; firma e ricevuta del manufatto non sostituiscono misura di accoppiamento.

## Manifest e workflow
requirement_id; intended_use = INERT_DEMO_ONLY; geometry_hash; revision; dimensions_required_mm[]; tolerance_intervals_mm[] (definiti dal docente per la specifica prova, non universali); print_profile_hash; material; orientation; machine_id_pseudonym; reported_measurements_mm[]; gauge_id; gauge_quality; operator_review; fit_test_status = NOT_TESTED | ACCEPTED_DEMO | REJECTED | UNKNOWN; measured_piece_id; superseded_revision.

Stati: REQUESTED → OPERATOR_APPROVED → PRINTED_UNVERIFIED → MEASURED → DEMO_FIT_ACCEPTED oppure REJECTED/UNKNOWN. Il solo slicer e il solo hash corretto non saltano il passaggio MEASURED + revisione. Verifica dimensioni indipendente dal file CAD; mantenere raw misura e criterio.

## Software immediato — progettato, non eseguito
Simulare 4 versioni CAD di una clip fittizia, 24 misure simulate con tolleranze **arbitrarie e dichiarate solo per il dataset sintetico**, 4 pezzi fuori tolleranza, 3 report incompleti, 2 mismatch di profilo/materiale, 4 arrivi fuori ordine e 2 ID di pezzo ambigui. Il validatore deve distinguere target, dimensione misurata, incertezza e revisione; non aggregare due pezzi come se fossero identici; non far passare automaticamente un risultato dimensionale senza test di incastro sul supporto inerte. Calcolare mismatch noti, false accettazioni, report mancanti e latenza applicativa simulata.

## Hardware necessario — non eseguito
3–4 schede LoRa, due PC, stampante 3D in laboratorio autorizzato, materiale approvato, almeno un calibro e supporto di accoppiamento innocuo. Acquisire le dimensioni fisiche, far provare l'incastro a un operatore e registrare non-conformità. Non trasmettere G-code eseguibile non revisionato e non azionare automaticamente la stampante tramite un messaggio DTN. Trasporto fisico con scheda pezzo. Misurare a parte trasferimenti e ricevute radio/applicative.

## Sicurezza, privacy, difficoltà
Progettazione con limiti di rischio; evitare elementi che reggono pesi, motori o isolamenti, lavorazioni pericolose e applicazioni senza supervisione. Le foto non devono contenere persone o ubicazioni private. ID di laboratorio, niente record sul tragitto degli studenti. File con hash e licenze, ruoli di autorizzazione, controllo di versione e conservazione breve. **Medium software / medium-high physical**, nessuna idoneità strutturale dichiarata.

## Anti-duplicazione
UC-047 gestisce scoperta e completamento di job di fabbricazione; UC-293 valuta in anticipo la compatibilità di ricambi con DNA/Romeo; UC-327 revisiona la leggibilità tattile di mappe; UC-315 tratta idoneità degli strumenti. **UC-333 aggiunge il controllo *a posteriori* del pezzo reale (dimensioni + fit test) collegato alla versione CAD e al profilo di stampa; un successo della stampante non è accettazione del pezzo.**