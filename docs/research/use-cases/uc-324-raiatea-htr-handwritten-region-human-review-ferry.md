# UC-324 — Raiatea: decifrare manoscritti storici offline senza inventare parole

**Stato (19 novembre 2026):** proposta di ricerca Raiatea/edge AI, non implementata né testata; nessun documento storico reale è stato importato. **Difficoltà:** alta (riconoscimento della scrittura, prova della lettura, diritti e revisione). Il PHY LoRa congelato, MAC, firmware e driver non cambiano.

## Problema e storia
Due laboratori scolastici vogliono rendere ricercabili copie **autorizzate** di lettere e quaderni manoscritti legati alla storia messinese. Il riconoscimento automatico della scrittura (HTR, handwritten text recognition) può confondere parole, abbreviazioni o nomi. Se la prima bozza viene indicizzata come trascrizione definitiva, Raiatea potrebbe citare una parola mai effettivamente scritta nel documento.

**Storia d'uso:** un docente o archivista vede l'immagine esatta del manoscritto, una bozza AI e i passaggi incerti; corregge o marca INDECIFRABILE. Solo la trascrizione autorizzata e revisionata può diventare fonte consultabile come tale. Anche una trascrizione accurata **non certifica** la verità storica di quanto narrato.

## Nodi e ruolo PollicinoNet
Archivista/titolare dei diritti, scuola di acquisizione, workstation HTR opzionalmente locale, revisori, catalogo Raiatea, 2–3 cache, relay degli studenti volontari. Esempio logico: immagine con diritti verificati conservata in un laboratorio di Milazzo, lavoro di revisione a Rometta e indice consultabile a Venetico. La consegna può avvenire in differita, senza presupporre che le sedi siano raggiungibili direttamente via LoRa.

PollicinoNet trasporta manifest, richieste di verifica, correzioni e versioni con identità esatta; non obbliga le scuole a spostare scansioni voluminose su LoRa. Le annotazioni sono *derivati* di uno specifico originale, non sostituzioni silenziose dell'originale.

## Bearer ammessi
- **LoRa:** soltanto stato di lavorazione, ID opachi, hash brevi ove compatibili con il protocollo esistente e richieste minime.
- **BLE:** piccoli metadati e rendezvous presso checkpoint autorizzati.
- **Wi-Fi/LAN/Internet:** immagini manoscritte, trascrizioni, modelli HTR e indici, secondo licenza e policy.
- **USB/SSD/trasporto fisico:** materiale voluminoso cifrato o pubblico fra sedi; verificare provenienza e integrità all'import.

## Contratto di prova
**SourcePage:** hash immagine originale, provenienza, licenza, policy di accesso, pagina/edizione, versione di digitalizzazione.

**TextRegion:** ID regione e coordinate nell'immagine originale, bozza HTR, ID/versione esatti del modello e del preprocessing, alternative di lettura, confidenza *non equiparata a certezza*, stato umano DRAFT / REVIEW_REQUIRED / HUMAN_VERIFIED / ILLEGIBLE / RESTRICTED, revisore autorizzato, hash del testo revisionato.

**SearchResult:** riga e regione originale, *stato visibile* della lettura, livello di permesso e versione di fonte. In caso di revisione successiva, l'indice precedente diventa STALE e non può presentare come verificata la vecchia lettura. Se cambiano pixel o ritaglio, la corrispondenza richiede una nuova verifica.

## Software subito — non ancora eseguito
Creare 8 pagine **artificiali** con 40 segmenti e testo noto, incluse parole deliberatamente ambigue, cancellature, sigle e porzioni illeggibili. Simulare due lavoratori HTR e due revisori virtuali; iniettare correzioni discordanti, foto riordinata, regione traslata, modello cambiato, hash non corrispondente, licenza revocata e replica che riceve prima la revisione e poi la bozza.

**Criteri PASS:** nessun DRAFT o ILLEGIBLE diventa fonte HUMAN_VERIFIED; ogni citazione porta all'esatta immagine/regione; contrasto fra revisori → CONFLICT, non media automatica; revoche e permessi applicati prima della ricerca; indice stale non risulta validato. Calcolare eventuale Character Error Rate (CER) **solo su ground truth fittizia** separata e dichiarata, non riportare accuratezza di modelli non testati. Nessun LLM è autorizzato a «completare» automaticamente parti mancanti come testo certo.

## Prove su hardware reale e territorio
Per la rete bastano 3–4 schede LoRa, due PC e due cache con Internet disabilitato nel braccio offline. Misurare trasferimento di manifest/ricevute e poi immagini via Wi-Fi/USB: byte per bearer, hash verificati, tempo alla revisione applicativa, copie revocate ancora osservabili. Nessuna conclusione sulla capacità radio provinciale senza misure.

Per l'HTR servono scansioni realmente autorizzate (preferire collezioni di pubblico dominio), revisori competenti, protocolli di trascrizione e valutazioni su campioni di controllo. Non pubblicare nomi o dati personali di soggetti potenzialmente viventi presenti in registri storici. Le scansioni possono contenere diritti e restrizioni anche se il supporto materiale è antico.

## Anti-duplicazione
**UC-099** è la pipeline generale di OCR/derivazione; **UC-296** ancora citazioni a versioni di PDF; **UC-312** lavora su audio e trascrizioni orali; **UC-305** controlla compatibilità degli embedding. Qui il nuovo contratto è la **lettura incerta di grafia storica, ancorata a coordinate dell'immagine, con adjudication umana e citazioni non promosse automaticamente**.

## Fonti di contesto
- Transkribus, metrica CER e confronto con ground truth: https://help.transkribus.org/character-error-rate-and-learning-curve
- IIIF, annotazione di una regione del manoscritto tramite Content State: https://iiif.io/api/cookbook/recipe/0485-contentstate-canvas-region/
