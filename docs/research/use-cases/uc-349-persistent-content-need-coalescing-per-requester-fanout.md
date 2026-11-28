# UC-349 — Aggregazione persistente delle richieste EXACT e consegna per richiedente

**Stato:** proposta documentale, 28 novembre 2026. Nessun test eseguito. Difficoltà media-alta. PHY LoRa congelato, MAC, driver e firmware invariati.

## Problema e user story
Tre laboratori vogliono lo stesso pacchetto didattico pubblico, presente in una sola cache. Se ogni richiesta attraversa separatamente il ponte opportunistico, può occupare più contatti e provocare copie inutili. Se invece il relay conserva soltanto l'hash dell'oggetto, può dimenticare due destinatari quando il primo annulla o riceve la risposta.

Come gestore di un checkpoint voglio aggregare richieste compatibili, mantenendo un registro persistente e limitato delle obbligazioni individuali, per scaricare il contenuto una volta quando possibile e consegnarlo separatamente a tutti i richiedenti ancora autorizzati.

## Attori, idoneità, scenario messinese
Tre cache scolastiche autorizzate (ad esempio Milazzo, Rometta e Venetico), un deposito di contenuti, un relay aggregatore, altri relay volontari, docente revisore. I contatti possono essere disgiunti e il relay può riavviarsi fra richiesta e risposta. Non serve il percorso inverso della richiesta: una cache autorizzata può soddisfare una richiesta ancora pendente al prossimo contatto. Nessuna copertura radio fra comuni è presunta.

## Contratti e bearer
- DISCOVERY: hint opaco di disponibilità o richiesta aggregata; non è prova di identità o autorizzazione.
- EXACT: hash/versione dell'oggetto, profilo di rappresentazione e ambito autorizzativo esatto. L'aggregazione si limita inizialmente a oggetti pubblici approvati, stesso dominio di fiducia e stessi vincoli di risposta. Il contenuto verificato può essere riusato; il singolo richiedente conserva ID, scadenza e stato.
- SEMANTIC: una richiesta "lezione Linux" non si fonde con una richiesta EXACT finché non è risolta in un oggetto esatto e autorizzato.

LoRa: hint, token e stati compatti entro il profilo esistente; BLE: inventario locale; Wi-Fi/Internet: oggetti; SSD/trasporto fisico: cache autorizzate. Nessun PDF intero su LoRa come requisito.

Schema logico (non formato radio): AggregateKey(object_hash, representation_id, policy_scope); Member(request_id, reply_capability, expiry, state, authorization_epoch); FetchAttempt(attempt_id, key, status); DeliveryReceipt(request_id, verified_hash, recipient, status). Conservare lo stato per membro e l'eventuale riferimento al blob. Un'annullamento autenticato chiude soltanto la richiesta corrispondente; nessuna estensione automatica della sua scadenza. Se il fetch è già partito, il blob può restare in cache secondo policy, non implica consegna. Un restart non deve risuscitare richieste chiuse. Se la tabella è piena, rifiuto esplicito o backpressure, non perdita silenziosa.

## Software immediato e criteri
Fixture: 6 nodi virtuali, 24 richieste (ripetizioni di tre oggetti, alcune versioni o policy incompatibili), finestre disgiunte, due cache, duplicati, annullamento di un solo membro, scadenza differente, riavvio prima/dopo fetch, risposta errata e retry. Confrontare inoltro separato vs aggregazione persistente sullo stesso trace e budget, contando richieste upstream, byte, occupazione di tabella, attese per membro e consegne applicative.
- PASS: annullare A non annulla B; una risposta ricevuta non marca tutti DELIVERED; il membro scaduto non riceve consegna; oggetti/hash/policy differenti non si fondono; il restart mantiene gli stati confermati; limiti di memoria e scadenze rispettati.
- Vantaggio da misurare, non requisito presunto: meno richieste e byte upstream senza penalizzare silenziosamente i membri con scadenze brevi. Aggregatori indipendenti possono ancora generare fetch duplicati; nessuna garanzia globale di unicità sotto partizione.

## Hardware, privacy e sicurezza
5–6 schede, 2–3 PC, cache con piccoli file pubblici/sintetici, contatti controllati A→relay→deposito e successivi contatti di ritorno separati. Verificare che Wi-Fi/Internet non aggirino la prova LoRa; distinguere hint, arrivo dell'oggetto e ricevute per destinatario. Misurare costi effettivi, registri e code senza modifiche radio.
Token di risposta pseudonimi e limitati alla campagna; non esporre al deposito liste di studenti o interessi sensibili. Autenticare richieste, cancellazioni e ricevute, applicare quote e retention, controllare autorizzazione anche al momento della consegna. Nessun GPS, itinerario o contenuto personale.

## Distinzione e riferimenti
UC-024 tratta ricerca e soppressione di duplicati di una richiesta, UC-083 sottoscrizioni durature e fan-out di notifiche, UC-088 fetch HTTP, UC-102 disseminazione push, UC-346 identità di eventi. Qui la novità verificabile è il ciclo di vita **individuale** di più richieste one-shot compatibili dietro un fetch condiviso, persistente durante disconnessione e crash.
L'aggregazione delle Interest in NDN è un precedente concettuale, non un'implementazione di PollicinoNet: https://doi.org/10.3390/s23031411 (2023); il lavoro avverte anche del rischio di aggregare richieste non equivalenti. Vedi https://arxiv.org/abs/1603.07995 per costi e limiti dello stato pendente.
