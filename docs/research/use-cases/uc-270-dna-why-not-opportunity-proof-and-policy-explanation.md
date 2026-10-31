# UC-270 — DNA «perché questa opportunità non compare?» con prove dei blocchi

**Stato:** proposta documentale del 31 ottobre 2026. Nessuna funzionalità DNA implementata per questo caso né risultato misurato. PHY LoRa congelato invariato. **Difficoltà:** alta (inferenza, autorizzazioni, percorsi alternativi e privacy).

## Problema risolto

DNA suggerisce opportunità combinando fatti distribuiti, domande e autorizzazioni. Un docente si aspetta di vedere un possibile scambio di sensori fra Rometta e Venetico, ma l'opportunità non appare. Le cause possibili sono molto diverse: manca una prova, un vincolo è **esplicitamente falso**, la prova è scaduta, l'utente non ha il permesso di vederla oppure un percorso alternativo è ancora praticabile. La risposta «non disponibile» non spiega il motivo e rischia di confondere assenza di dato e negazione.

**User story:** come tutor FSL voglio conoscere, nei limiti dei miei permessi, **perché** una certa opportunità non è attualmente dimostrata, senza che il sistema inventi fatti o riveli dati segreti.

## Attori, nodi e scenario

Client scolastico richiedente; motore regole DNA; detentori di fatti (due laboratori); revisore autorizzato; cache e relay PollicinoNet nei checkpoint Rometta/Venetico; eventuale GeoTopic per il discovery. Un messaggio differito può aggiornare un blocco già spiegato; la spiegazione precedente conserva l'ID/versione della fotografia dei fatti usata. I relay studenti non leggono né decidono sulle premesse private.

Esempio: disponibilità del sensore TRUE, bisogno TRUE, calibrazione UNKNOWN, permesso al prestito FALSE. Una spiegazione autorizzata indica che l'offerta **non è proponibile** a causa del permesso esplicitamente negato e che la calibrazione rimane ignota. Non trasforma `UNKNOWN` in `FALSE`, né svela il detentore di un vincolo privato.

## Contratto di dati / distinzione semantica

`goal_id`, `goal_version`, `rule_id`, `rule_version`, `facts_snapshot_hash`, `visible_premise_refs`, `proof_status`, `blocker_classes[]`, `alternative_derivation_ids[]`, `privacy_policy_version`, `expires_at`. Stati di premessa: `VERIFIED_TRUE`, `VERIFIED_FALSE`, `UNKNOWN`, `UNVERIFIED`, `EXPIRED`, `ACCESS_DENIED`, `CONFLICTED`.

La spiegazione **non è una prova che la collaborazione sia impossibile in assoluto**. È relativa a versioni note di regole/fatti e alle autorizzazioni del richiedente. Se una premessa non è visibile, mostrare un messaggio generico conforme alla policy (anche senza confermare che esista una premessa sensibile). Per più derivazioni possibili, spiegare **tutti i percorsi rilevanti** entro un limite di complessità, evitando di presentare un unico blocco come causa esaustiva. Le «modifiche minime necessarie» sono ipotesi, non azioni autorizzate.

## Perché PollicinoNet e bearer

Il motivo dell'assenza cambia quando arrivano nuovi fatti o revoche da scuole intermittenti. PollicinoNet trasporta oggetti firmati e legati a versioni; il motore applicativo DNA calcola spiegazioni, **non** il relay.

- **LoRa:** ID di obiettivo, digest di snapshot e annuncio di revisione, soltanto se compatibile con dimensione e policy.
- **BLE:** metadati autorizzati e risposte limitate vicino a checkpoint.
- **Wi-Fi / Internet:** fatti RDF, report SHACL, grafo delle dipendenze e spiegazioni complete.
- **USB / SD / trasporto fisico:** evidenze e grafo sensibili su supporti autorizzati.
- `DISCOVERY` annuncia aggiornamenti; `EXACT` lega fatti, regole e policy a una versione; `SEMANTIC` produce motivazioni condizionate da evidenza e accessi.

## Test software senza hardware

Tre processi Python isolati, 3 regole di matching e 30 fatti sintetici; primi test su regole deterministiche, non servono LLM. Prove obbligatorie: (1) solo `UNKNOWN`; (2) premessa `FALSE`; (3) fatto scaduto; (4) due derivazioni alternative, una bloccata e l'altra valida; (5) prova firmata da fonte non autorizzata; (6) revoca e replay; (7) policy di accesso che non deve permettere inferenze sull'esistenza di fatti riservati; (8) regole cicliche, troncamento spiegazione marcato esplicitamente.

**Criteri PASS:** nessun `UNKNOWN` presentato come falso; nessuna opportunità approvata senza prove; motivazioni riproducibili per snapshot e versione; revoche invalidano la spiegazione precedente; confronto differenziale fra vista autorizzata e non autorizzata non rivela struttura protetta; limite computazionale esplicito.

Misurare numero di premesse ispezionate, dimensione dei messaggi, latenza simulata di aggiornamento e falsi «bloccato» sulle fixture. Un LLM può in futuro **riassumere** motivazioni già validate, ma non può modificarne lo stato logico.

## Prove fisiche e limiti

Iniziare su due PC scollegati e un relay simulato. Dopo verifica software, 4–6 schede con checkpoint scolastici autorizzati: LoRa porta un digest di revisione, Wi-Fi/USB la modifica del fatto e la prova. Registrare tempi di trasporto reali, provenienza, conferma applicativa e eventuali periodi con spiegazione obsoleta. Nessuna prestazione fisica è ancora disponibile. Non utilizzare deduzioni automatiche per assegnare risorse senza autorizzazione umana.

## Privacy e sicurezza

Minimizzazione, controllo degli accessi **prima della costruzione della spiegazione**, politiche di non-enumerazione, firme, scadenze, audit accessibile solo ai revisori, cifratura di fatti privati e limiti alle richieste per impedire probing. Nessun profilo o bisogno personale negli annunci pubblici.

## Anti-duplicazione

- **UC-244** spiega **perché un'opportunità è stata derivata**; UC-270 spiega **perché quella attesa non compare**.
- **UC-260** formula domande mirate per premesse mancanti; UC-270 produce una spiegazione leggibile, **senza emettere automaticamente nuove query** e distinguendo negazioni esplicite, scadenze e blocchi di policy.
- **UC-251** riconosce bisogni dalle domande senza trasformarli in fatti; UC-270 interroga risultati e vincoli di inferenza, non estrae bisogni.
- **UC-186/258** riguardano fonti documentali Raiatea, non l'assenza di una deduzione DNA.

Riferimento concettuale: [Why-Not Provenance, Università di Stoccarda](https://www.ipvs.uni-stuttgart.de/departments/de/research/projects/why_not/). Non si afferma che PollicinoNet abbia già un motore why-not.
