# UC-329 — Raiatea: georeferenziare mappe storiche senza inventare precisione

**Stato (21 novembre 2026):** proposta documentale; nessuna carta storica importata, nessun risultato GIS calcolato e nessun trasferimento reale provato. **Difficoltà:** medio-alta per il simulatore, alta per fonti storiche, metodi GIS e revisione umana. Nessuna modifica al PHY LoRa congelato né allo stack radio.

## Problema e storia
Due classi vogliono confrontare una carta storica autorizzata della provincia di Messina con una base moderna. L'immagine storica può avere scala imprecisa, proiezione sconosciuta o edifici spostati/scomparsi. Se un algoritmo allinea bene alcuni punti ma male gli altri, l'interfaccia potrebbe mostrare una precisione inesistente e attribuire a un luogo moderno un'informazione storica sbagliata.

**Risultato utile:** Raiatea distribuisce originale, punti di controllo, trasformazione, revisione e *incertezza visibile*, impedendo che una mappa approssimativa diventi una carta di navigazione o una fonte geografica certa.

## Attori e scenario scolastico
Biblioteca/archivio titolare, docente di storia/geografia, revisore GIS, due laboratori (es. Milazzo e Rometta), un catalogo Raiatea, cache scolastiche e relay volontari. Prima una mappa completamente fittizia, poi eventualmente una mappa storica con diritti e provenienza chiari. Nessun movimento di studenti tracciato; nessun collegamento radio fra comuni dato per scontato.

## Perché PollicinoNet
Il raster può essere grande e restare in una cache; le altre sedi devono conoscere l'**identità esatta** dell'originale e della revisione, richiedere i dati e ricevere i pareri in differita. DISCOVERY/EXACT/SEMANTIC descrivono le richieste informative, non mezzi radio.

**MapGeoRefPack proposto:** source_raster_hash, title/date/edition, holding_institution, license, image_rights, target_CRS, transformation_kind_and_version, control_points_with_review_status, independent_checkpoints, method_parameters, residuals, withheld_validation_error, uncertainty_scope, reviewer_state (DRAFT/UNVALIDATED/REVIEW_REQUIRED/APPROVED_FOR_EDUCATION/REJECTED), derived_raster_hash, history, supersedes. Una coordinate pair non verificata rimane contestata, non viene appiattita in una media.

**Bearer:** LoRa solo per ID opachi, manifest minimi e richieste; BLE per metadati presso checkpoint; Wi-Fi/Internet per raster, tile, log GIS e revisioni; USB/SSD/trasporto fisico per scansioni e pacchetti voluminosi, verificati prima dell'importazione.

## Software subito — test proposto, non svolto
Costruire una carta **sintetica** di 12 punti noti e distorti: 6 punti di controllo, 3 punti di validazione *tenuti fuori dalla stima*, 3 punti ambigui o cambiati. Confrontare una trasformazione affine riproducibile e una scelta ingenua di landmark; simulare una coordinate pair errata, origine CRS sbagliata, punti tutti concentrati in un angolo, un ramo revisionato offline in conflitto, due scansioni con hash diversi e una licenza assente.

**Criteri PASS attesi:** (1) non riportare errore calcolato sui punti usati per adattare il modello come unica misura della qualità; (2) checkpoint indipendenti e incertezza devono accompagnare la mappa; (3) GCP contestato -> REVIEW_REQUIRED; (4) fonte, licenza o CRS mancanti -> non APPROVED; (5) una nuova revisione non modifica silenziosamente un raster derivato già citato; (6) vecchie versioni restano marcate STALE. Metriche: errore su holdout sintetico, quota rifiuti corretti, percentuale di versioni con fonte e revisione esatta. Non riferire accuratezza geografica reale.

## Prova hardware successiva
3–4 schede LoRa e 2 PC in banco per annuncio manifest, richiesta, copia per relay e conferma dell'esatto pacchetto; niente raster via LoRa salvo dimostrazione dimensionale pienamente compatibile con il trasporto esistente. Poi laboratorio GIS con QGIS o equivalente e confronto indipendente, usando dapprima mappe inventate. Soltanto con fonti licenziate e revisori competenti, un progetto sulla cartografia storica messinese.

**Misure separate:** TX e RX radio per ciascun hop reale, ricevuta applicativa, dimensioni/byte per bearer, latenza di propagazione della revisione, errore georeferenziato valutato su punti indipendenti. Non sovrapporre misure simulate e fisiche.

## Privacy, sicurezza e limiti
Non pubblicare mappe di abitazioni, luoghi privati sensibili o percorsi degli alunni; controllare licenze di scansioni e base cartografica, provenance, firme degli esiti e permessi delle cache. Le carte storiche non sono indicazioni per soccorso, evacuazione, mobilità o navigazione moderna. Il modello AI/GIS non può inventare un punto di controllo o promuovere automaticamente una ricostruzione storica a fatto verificato.

## Non duplicazione
UC-017 tratta trasporto di tile offline; UC-122 modifica collaborativamente feature geospaziali; UC-296 cita versioni PDF; UC-324 riguarda lettura di *scrittura manoscritta*; UC-327 fabbricazione di mappe tattili. **Qui la specifica nuova è il georiferimento di una fonte cartografica storica con checkpoint indipendenti, errore dichiarato e revisione scientifica/diritti.**

## Fonti di contesto
- *Historical Collaborative Geocoding* (2018), distribuzione e qualità dei ground control points: https://www.mdpi.com/2220-9964/7/7/262
- Esri ArcGIS Pro, valutazione degli errori e dei punti di controllo: https://learn.arcgis.com/en/projects/georeference-imagery-in-arcgis-pro/
