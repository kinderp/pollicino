# UC-332 — Microscopia tra scuole: scala verificabile, fuoco e dataset AI

**Stato:** proposta documentale del 22 novembre 2026, non implementata. **Priorità:** alta per Raiatea, laboratori, dataset e AI. **Difficoltà:** medio-alta software; alta per validazione strumentale e interpretazione biologica.

## Problema in parole semplici
Una foto al microscopio può apparire nitida, ma senza una **scala affidabile** non sappiamo quanto è grande l'oggetto. Cambiare obiettivo, camera, dimensione immagine o ritagliare e ridimensionare senza aggiornare i metadati rende inesatte le misure. Una classificazione AI può aggiungere un'etichetta incerta. Se scuole diverse condividono immagini offline, ogni scuola deve sapere quali immagini sono adatte a misure e quali servono solo per osservare.

OME propone metadati sperimentali per riproducibilità: https://docs.openmicroscopy.org/ome-model/6.2.3/specifications/index.html ; un esempio pratico di calibrazione per obiettivo e configurazione è https://www.scalebar.app/learn/stage-micrometer-calibration . Non si assume che una fotocamera o un microscopio scolastico supporti OME nativamente.

## Attori, nodi e scenario messinese
Docente di scienze, laboratorio di microscopia a Milazzo, gruppo revisore a Venetico/Rometta, cache Raiatea, PC edge-AI opzionale, 3–4 schede relay e studenti volontari. Prima immagini e campioni **artificiali**, poi eventualmente preparati didattici non pericolosi (es. fili/fibre/materiali inerti) sotto supervisione. Niente immagini mediche, campioni umani, organismi patogeni o dati personali.

## Perché PollicinoNet
Un laboratorio rende nota la presenza di un'immagine/manifest; il file originale e le revisioni viaggiano più tardi via Wi-Fi o supporto fisico. Una correzione della calibrazione può arrivare *dopo* una classificazione AI: la rete deve invalidare le conclusioni dipendenti dai metadati errati senza riscrivere il file originale. Raiatea indicizza soltanto le varianti autorizzate e conserva le citazioni al file e alla regione d'immagine esatti.

## Bearer
- **LoRa:** ID immagine/dataset, hash del manifest, stato revisione, richiesta di calibrazione e ricevute; mai immagini raw estese.
- **BLE:** metadati compatti e piccoli controlli di prossimità.
- **Wi-Fi/Internet/LAN:** TIFF/PNG originali, metadati, annotazioni e modelli AI quando autorizzati.
- **USB/SD/trasporto fisico:** fotografie/slide dimostrative tra laboratori con ricevuta; nessuna credenziale su supporto non protetto.

## Manifest e stati
image_id; raw_sha256; native_width_px; native_height_px; objective_id; camera_id; camera_binning; capture_profile_hash; pixel_size_um_per_px; calibration_method; calibration_evidence_sha; crop_resize_transform; focus_quality_manual_or_estimated; scale_status = VERIFIED | UNVERIFIED | INVALID; classification_proposal; classification_model_hash; human_review_status; license_permission; source_version; reviewer_signature_if_supported.

Le etichette AI non sono identificazioni certificate. Una scala **non verificata** permette visualizzazione descrittiva, ma non pubblicazione di misure dimensionali come risultati accertati. Le misure dipendono dalla configurazione esatta, non dal solo valore nominale di ingrandimento dell'obiettivo.

## Software immediato — solo piano, non eseguito
Generare 12 immagini sintetiche geometriche con dimensioni campione note, 3 profili ottici fittizi, 4 crop, 4 resize, 3 immagini sfocate e 3 manifest con scala incoerente. Creare 12 classificazioni AI **simulate** di cui 4 sbagliate. Il validatore deve:
1. associare l'immagine all'hash originale, ai parametri di acquisizione e alla calibrazione corretta;
2. distinguere crop puro (scala per pixel invariata) e resize (scala per pixel modificata), evitando doppie trasformazioni;
3. non sostituire mai misura fisica con un rapporto AI; conservare suggestion + revisione;
4. rendere STALE una misura derivata dopo correzione del profilo/calibrazione;
5. segnalare dati mancanti come UNKNOWN, senza fingere precisione.
Confrontare mismatch individuati, falsi positivi, completezza e byte di manifest; niente prestazioni del microscopio dichiarate.

## Hardware reale — non eseguito
Microscopio ottico scolastico e fotocamera/USB camera, **micrometro da tavolino** o riferimento metrologico appropriato, campione innocuo, 2 PC, 3–4 LoRa. Acquisire immagini a più obiettivi e configurazioni e verificare la scala in modo indipendente, tenendo gli originali. Testare poi solo l'inoltro opportunistico dei manifest, e il successivo recupero delle immagini con Wi-Fi/USB. Un esperto convalida qualsiasi conclusione scientifica; nessuna diagnosi.

## Privacy, sicurezza, diritti
Solo materiale creato a scuola/autorizzato, licenze esplicite, nessun volto o tessuto umano; controlli di accesso su immagini e annotation pack, hash e versioni immutabili, revisione umana. Nessun percorso degli studenti conservato. LoRa PHY, MAC, firmware e driver congelati restano immutati.

## Anti-duplicazione
UC-099 distribuisce artefatti di ingestione Raiatea; UC-187 coordina esperimenti scientifici ripetibili; UC-204 lega provette e dati; UC-209 raccoglie disaccordi di annotazione; UC-314 documenta foto-quadrat costieri. **UC-332 presidia specificamente la scala metrica per pixel, la trasformazione crop/resize e la validità di misure e label AI nelle microfotografie.**