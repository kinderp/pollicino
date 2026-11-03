# UC-279 — Caricamento sicuro di modelli AI trasportati offline

**Stato:** proposta documentale del **3 novembre 2026**, non implementata; nessuna prova software/hardware eseguita. **Difficoltà:** alta (supply chain, isolamento runtime e policy offline). PHY LoRa congelato, MAC/driver/firmware invariati.

## Problema e user story

Una classe di Rometta riceve tramite data mule un modello AI generato da un laboratorio di Venetico. Il file ha l'hash corretto, e una firma dimostra chi l'ha distribuito. Ma **un artifact autenticato può comunque contenere codice eseguibile o un formato pericoloso da deserializzare**, oppure riferirsi a dipendenze non autorizzate. Un import automatico potrebbe quindi essere rischioso anche se il trasporto PollicinoNet è perfetto.

**Come docente che gestisce i modelli AI del laboratorio**, voglio che il contenuto resti in **quarantena non eseguibile** fino a verifica del formato, delle dipendenze, della policy e dell'ambiente autorizzato, evitando di lanciare codice non fidato mentre ispeziono il pacchetto.

## Attori, nodi e perché PollicinoNet

Editore autorizzato di modelli, laboratorio destinatario con PC o Raspberry Pi, revisore tecnico/docente, cache P2P, 4–6 relay fra checkpoint di Messina, Villafranca, Rometta e Venetico, eventuale nodo edge AI. La rete distribuisce **stati di revisione piccoli e firmati** separati dai file di grandi dimensioni. I relay non eseguono modelli, non scansionano contenuti cifrati e non attribuiscono fiducia a un file solo perché è stato inoltrato correttamente.

Il caso usa `DISCOVERY` per annunciare un candidato, `EXACT` per legare **file bytes, manifest, dipendenze, ambiente e revisione** e `SEMANTIC` per dichiarare capacità desiderata senza bypassare la policy.

## Bearer

- **LoRa:** digest autorizzato del manifest, `QUARANTINE`/`REVIEW`/`APPROVED_FOR_SANDBOX`/`REVOKED` (con epoch, firma e limite di dimensione), mai pesi grandi.
- **BLE:** negoziazione locale di metadati e stato di import.
- **Wi-Fi / LAN / Internet:** modelli, tokenizer, manifest, log di verifica; download autorevole solo quando possibile.
- **SSD/USB gestito e trasporto fisico:** file di grandi dimensioni cifrati/verificati. Nessuna esecuzione automatica dal supporto.

## Contratto applicativo proposto

`ModelImportManifest = {artifact_sha256, files:[path,sha256,size,format], publisher_signature, lineage, runtime_and_version, dependencies_lock, trust_remote_code_required, license_policy, authorized_purpose, review_epoch}`.

`ImportDecision = {artifact_sha256, manifest_sha256, importer_version, decision, reason_codes, reviewer_role, policy_epoch, expiry, signature}`.

Stati: `ARRIVED_INERT`, `PENDING_FORMAT_CHECK`, `QUARANTINED`, `REQUIRES_HUMAN_REVIEW`, `APPROVED_FOR_SANDBOX`, `REVOKED`. Un `APPROVED_FOR_SANDBOX` autorizza al massimo una prova **in un ambiente isolato** con risorse e rete ristrette: non equivale ad approvare il modello per produzione, accuratezza o fairness.

**Regole di base:** percorso e archivio normalizzati (niente path traversal o symlink fuori root); limiti su dimensioni, decompressione e consumo; verificare hash/firme/licenze; allineare autorizzazione a file, versione di importer e runtime; default-deny per formati con esecuzione implicita (es. pickle), script e import di codice remoto; consentire solo formati e loader esplicitamente approvati per il prototipo, senza garanzia assoluta di sicurezza. Isolare i parser di artefatti non fidati; evitare auto-execute di hook, plugin, installer e notebook.

## Esperimento software riproducibile, senza eseguire contenuti pericolosi

1. Creare **pacchetti toy e interamente inerti**, con manifest validi/invalidi, formati ammessi/non ammessi, path simulati `../escape`, dimensioni dichiarate false, modelli senza tokenizer, loader che richiederebbe `trust_remote_code`, firma scaduta.
2. Implementare un verificatore **di soli metadati** (non `pickle.load` e non esecuzione del modello) con decisioni deterministiche.
3. Simulare tre cache partizionate; far arrivare modello prima della revisione, poi una revoca o aggiornamento della policy, e verificare che non si esegua alcun import mentre lo stato è `PENDING`/`REVOKED`.
4. Consentire soltanto un *toy tensor* in formato dati esplicitamente approvato in sandbox con filesystem limitato, non privilegiato e senza accesso ai dati degli studenti. Non affermare che la sandbox garantisca sicurezza assoluta.
5. Confrontare tre policy: auto-load ingenuo (**simulato, mai eseguito**), hash/firma soltanto, gate formato+policy+isolamento; conteggiare decisioni di blocco corrette, falsi blocchi, ri-import dopo revoca, tempi e byte.
6. Salvare fixture, seed, versione del validatore, report `PASS/FAIL/UNKNOWN/NOT_TESTED`. Test di supply chain **non** uguale a valutazione dei comportamenti o dei bias del modello.

**Criteri PASS:** contenuto privo di autorizzazione resta inert; una firma valida non bypassa un formato non ammesso; manifest alterato o con percorsi insicuri viene rifiutato; una revoca arrivata in ritardo impedisce *nuove* esecuzioni; le esecuzioni eventualmente già avvenute non possono essere annullate retroattivamente.

## Prova fisica

Due PC/Raspberry Pi di laboratorio e 4–6 schede LoRa **solo** per metadati/richieste/stati compatti con adapter attuale. Trasferire un modello toy innocuo via Wi-Fi o SSD autorizzato. Indurre partizione e arrivo tardivo di `REVOKED` con test controllato; verificare sul nodo edge che la decisione vigente sia rispettata prima dell'import, raccogliendo ricevute EXACT e log di stato. Non utilizzare file malevoli né credenziali reali. La prova fisica è una verifica di sincronizzazione e workflow, **non** una certificazione di sicurezza del runtime o del modello.

## Privacy, sicurezza e difficoltà

Niente dati di studenti, ruoli minimizzati, log non sensibili, chiavi isolate dal relay, policy versionata e minimo privilegio. Proteggere anche i digest di modelli privati da esposizione pubblica (vedi UC-278). Se il dispositivo non può creare un ambiente isolato affidabile, bloccare l'import finché non è disponibile un host appropriato. **Alta**: è facile trasportare i byte, molto meno definire una catena di fiducia per eseguirli.

## Confronto anti-duplicati

**UC-004** distribuisce modelli; **UC-085** seleziona variante e runtime; **UC-180** controlla autorizzazione e integrità generale dei pacchetti; **UC-225** indaga la contaminazione dei dataset; **UC-246** isola le istruzioni nei documenti RAG. **UC-279 riguarda specificamente il momento in cui un file di modello diventa codice o dati caricati nel runtime**, e il rischio di deserializzazione/esecuzione implicita che hash e firma non neutralizzano.

## Fonti utili (non misure della rete)

- Hugging Face, *Pickle Scanning*: https://huggingface.co/docs/hub/security-pickle — ricorda i limiti dei controlli statici e i rischi di deserializzazione.
- Hugging Face, *Text Generation Inference model safety*: https://huggingface.co/docs/text-generation-inference/main/en/basic_tutorials/safety — distingue formati dati e loading con `trust_remote_code`.
