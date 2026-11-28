# UC-351 — Dataset AI offline: divisione di classi e riannotazione selettiva

**Stato:** proposta documentale, 28 novembre 2026. Nessuna migrazione o addestramento eseguiti. Difficoltà medio-alta/alta. PHY LoRa congelato, MAC, driver e firmware invariati.

## Problema e user story
Tre laboratori costruiscono un dataset di forme geometriche. Nella tassonomia V1 esiste la classe "quadrilatero"; V2 distingue rettangolo (in questo esempio anche il quadrato) e altro quadrilatero. Un'etichetta V1 non contiene necessariamente le informazioni per scegliere la classe figlia. Rinominare il codice oppure copiare il vecchio label in entrambe le classi può falsare addestramento e metriche.

Come responsabile del dataset voglio distribuire una tassonomia revisionata e richieste mirate di riannotazione ai nodi che conservano le evidenze, preservando le etichette originali e dichiarando quali campioni non sono ancora utilizzabili per la valutazione V2.

## Attori e scenario Messina
Laboratori scolastici di Milazzo, Venetico e Spadafora, ciascuno con copie diverse di immagini sintetiche, docente curatore, revisori, cache Raiatea e relay volontari. Una scuola può ricevere V2 prima delle immagini originali, oppure ricevere una vecchia annotazione dopo V2. Non serve spostare l'intero dataset per sapere quali esempi richiedano revisione.

## PollicinoNet, contratti e bearer
DISCOVERY: ID tassonomia/versione, riepilogo delle classi toccate, disponibilità di una revisione; EXACT: hash di esempio, tassonomia sorgente/destinazione, definizione della classe, mapping approvato, revisione e identità logica dell'annotazione; SEMANTIC: relazione più ampia/più stretta, non equivalenza. LoRa per manifest e ticket compatti; BLE per metadati; Wi-Fi/Internet/USB/trasporto fisico per immagini, linee guida e dataset esatti, sempre autorizzati.

Schema logico: Taxonomy(version_hash, class_id, definition); Mapping(from_hash,to_hash,old_class,relation,candidates,review_hash); Annotation(sample_hash,taxonomy_hash,class_id,evidence_ref,review_state); ReannotationTicket(sample_hash,target_taxonomy,policy,expiry); DatasetManifest(taxonomy_hash,split_ids,accepted_labels,unresolved,policy_hash).
Per classi realmente equivalenti, mapping automatico solo con regola approvata. Per split uno-a-molti senza evidenza discriminante, stato NEEDS_REANNOTATION; se immagine assente EVIDENCE_MISSING; conflitti REVIEW_REQUIRED. Nessuna inferenza del figlio dal solo codice vecchio; un classificatore può proporre una bozza ma non certificare il ground truth. Una correzione deve legarsi all'esatta evidenza e guida V2. Non sostituire la label storica. Unire classi solo con regola documentata e mantenere metriche comparabili soltanto sotto definizioni coerenti.

## Software immediato
60 esempi sintetici, 3 cache, classi equivalenti, merge e split; 2 versioni della guida, 12 esempi senza evidenza disponibile in una cache, etichette tardive e duplicate, conflitti e un mapping disapprovato. Costruire un manifest V2 con campioni risolti e irrisolti; testare che un'etichetta V1 tardiva non sovrascriva quella V2 approvata. Confrontare baseline di rinomina automatica con migrazione verificata contando falsi mapping e lavoro di riannotazione. Tenere fisso il test set per confronti legittimi o dichiarare separatamente cambiamento del denominatore; nessun risultato di accuratezza presunto. Non selezionare il test set sulla base della facilità di riannotazione.
PASS: ogni split privo di evidenza resta irrisolto; nessuna promozione automatica di bozza AI; ogni manifest indica campioni esclusi, versioni e motivo; rettifiche e duplicati non alterano le partizioni train/test in modo implicito.

## Hardware e sicurezza
4–5 schede, 2–3 PC, immagini di forme generate localmente e app di annotazione semplice. Trasportare prima manifest e ticket con LoRa, poi immagini selezionate via bearer ricco e ritorno delle decisioni. Separare esito di rete da correttezza della label. Successivamente applicabile a classificazione non sensibile di materiali o componenti robotici, con autorizzazione e campioni adeguati.
Nessun volto, voce, profilo studente o dato sensibile. Autenticazione di mapping e annotazioni, minimizzazione dei digest (UC-278), quote, revoca secondo policy, conservazione della provenienza e revisione umana. Nessuna esecuzione automatica di modelli ricevuti (UC-279).

## Distinzione e riferimento
UC-032 seleziona esempi incerti, UC-209 tratta disaccordo tra annotatori, UC-115 mappa ontologie, UC-135 migra schemi, UC-282 separa epoche di modello. Qui il trigger è la perdita di informazione semantica nella divisione di una classe, e il criterio è la composizione di un nuovo dataset con riannotazione selettiva e denominatori espliciti.
W3C SKOS Reference, sezione 10, distingue mapping gerarchici ed equivalenza: https://www.w3.org/TR/2009/REC-skos-reference-20090818/ . È un riferimento semantico, non una specifica di migrazione dei dataset.
