# UC-328 — Apiario didattico: conteggi di ingresso/uscita con qualità esplicita e ferry LoRa

**Stato (21 novembre 2026):** proposta di ricerca, nessun apiario, sensore o algoritmo PollicinoNet provato. **Difficoltà:** media per il validatore sintetico; alta per il conteggio e l'esperimento non invasivo sul campo. PHY LoRa congelato, MAC, driver e firmware invariati.

## Problema e risultato desiderato
Un contatore ottico o video all'ingresso di un alveare può confondere un'ape che torna indietro con due passaggi, perdere animali in rapida successione o produrre errori con luce e umidità variabili. La rete può consegnare fedelmente un valore **tecnicamente ricevuto ma biologicamente errato**. Serve conservare, per ciascuna finestra, il conteggio *stimato*, la qualità della misura e la procedura di validazione, senza dedurre automaticamente salute o mortalità della colonia.

**Storia concreta:** un apicoltore autorizza l'osservazione esterna di un suo apiario. Il logger locale conta ingressi e uscite in finestre aggregate; il checkpoint scolastico ne apprende gli eventi compatti quando un relay volontario incontra la stazione. Un docente confronta un piccolo campione di finestre con un riferimento di conteggio supervisionato.

## Attori e rete messinese
Apicoltore responsabile; sensore/edge logger senza attuazione; checkpoint scolastico; studenti volontari come relay store-and-forward; docente/revisore; due cache. Scenario *ipotetico*: osservazione autorizzata nell'hinterland di Rometta e revisione a Milazzo/Venetico, senza pretendere copertura diretta né pubblicare coordinate esatte dell'apiario. Non assegnare studenti ad accessi fisici agli alveari.

## Perché PollicinoNet e contratti
Le finestre riassuntive sono piccole, il video grezzo è voluminoso e non va trasmesso via LoRa. La custodia differita evita di perdere le osservazioni quando Internet manca, ma non trasforma una stima in un censimento certo.

**BeeWindow proposto:** station_pseudonym, sensor_epoch, sequence, time_window, clock_quality, in_estimate, out_estimate, count_method, model_or_threshold_version, ambient_context_if_measured, quality_flags, review_state (RAW/LOW_CONFIDENCE/REFERENCE_CHECKED/UNKNOWN), evidence_hash, signature_or_authenticated_origin. Non pubblicare dati di localizzazione puntuale; conservare campioni video solo se autorizzati e necessari.

**Bearer:** LoRa per micro-record, digest e richieste compatibili con l'adapter e i suoi limiti attuali; BLE per raccolta locale; Wi-Fi/LAN/Internet per dashboard, video selettivo e report; SD/USB/trasporto fisico per campioni di validazione cifrati o espressamente pubblicabili.

## Software subito — piano riproducibile (non eseguito)
Creare **160 eventi artificiali** (120 attraversamenti con verso noto e 40 movimenti ambigui o disturbi), raggruppati in 24 finestre. Iniettare: un'ape che entra ed esce, inversione di direzione prima del passaggio, passaggi ravvicinati, timeout sensore, cambi di modello, clock non affidabile, riavvio, ritardi, duplicati e arrivo fuori ordine. Confrontare una somma ingenua dei trigger e un validatore a stati.

**Criteri di accettazione da implementare:** (1) il doppio invio dello stesso (station_epoch, sequence, hash) non raddoppia i conteggi; (2) UNKNOWN e LOW_CONFIDENCE non diventano osservazioni verificate; (3) per dati sintetici con ground truth si riportano errore assoluto e matrice di confusione per verso; (4) cambi di modello non si fondono senza etichetta; (5) le ricevute sono distinte da una verifica biologica. Un record parziale va conservato come parziale, non imputato a zero.

## Hardware e prova fisica
Fase 1: banco senza animali, con sensore di passaggio o video sintetico riprodotto localmente e **3–4 schede LoRa + 2 PC**; finestra LoRa di dati compatti, perdita di un contatto e successivo recupero via relay. Registrare TX, RX, hash, ricevute applicative e bearer effettivo per hop.

Fase 2 **solo con un apicoltore competente e autorizzazione**, collocare un supporto esterno che non ostruisca il volo né modifichi l'alveare, con alimentazione elettrica sicura e senza illuminazione o azioni stressanti. Affiancare un conteggio manuale indipendente su finestre brevi concordate; misurare luce, condizioni e scarti per ciascun metodo. Non presupporre l'esattezza di un modello di edge AI né capacità radio intercomunali. Interrompere la prova se disturba le api o l'attività dell'apicoltore.

## Privacy, sicurezza e limiti
Nessun volto, voce, nominativo, percorso degli studenti o coordinate dell'apiario rese pubbliche; accessi al video controllati, retention minima e consenso/autorizzazione espliciti. Non dichiarare rischio fitosanitario, mortalità, produttività o sicurezza ambientale sulla sola base del traffico. Mai comandi di apertura/chiusura o intervento sull'alveare. Crittografia/autenticità delle capsule e verifica della versione del metodo sul destinatario.

## Differenza dai casi esistenti
UC-003 trasporta sensori rurali in generale; UC-273 trasporta *eventi bioacustici* senza audio; UC-314 tratta foto-quadrat di biodiversità; UC-309 riguarda qualità di misure PM. **Qui l'oggetto nuovo è il conteggio direzionale non invasivo di passaggi rapidi con falsi trigger, revisione di ground truth e aggregazione intermittente.**

## Fonti orientative, non risultati PollicinoNet
- American Bee Journal (2024), *Bee Counter Design to Reduce Counting Errors and Facilitate Validation*: https://americanbeejournal.mydigitalpublication.com/articles/bee-counter-design-to-reduce-counting-errors-and-facilitate-validation
- Odemer et al. (2024), problemi dei contatori automatici e limiti video: https://onlinelibrary.wiley.com/doi/full/10.1111/jen.13256
