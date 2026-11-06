# UC-287 — Biblioteca dei semi scolastici: lotti, germinazione e risultati differiti

**Stato:** proposta documentale del **6 novembre 2026**. Non implementata; nessun test software/fisico, nessuna misura agronomica. **Difficoltà medio-alta.** PHY LoRa congelato, MAC, driver e firmware invariati.

## Problema concreto

Due orti scolastici possono voler condividere piccoli *lotti dimostrativi* di semi autorizzati e confrontare esperimenti di germinazione. Il solo messaggio «semi disponibili» non dice nulla sulla provenienza dichiarata del lotto, la data, la quantità effettivamente consegnata o **quante piantine siano realmente germinate su quante semine valide**. Gli studenti potrebbero scambiare dati in ritardo: un risultato tardivo non deve essere associato al lotto sbagliato, e una prova non ancora conclusa non diventa un risultato negativo.

**Scenario:** laboratori didattici di Rometta, Venetico e Spadafora effettuano esercitazioni supervisionate; un relay studente volontario porta annunci sintetici tra i checkpoint e la scatola di semi può muoversi **fisicamente solo tra scuole con autorizzazione**. Prima fase rigorosamente con lotti e misure sintetici.

## Attori e perché PollicinoNet

Docenti di scienze/informatica, responsabili degli orti, magazzino e postazione di germinazione, relay e cache scolastiche, revisore delle osservazioni. PollicinoNet separa l'annuncio compatto `lot_id` dal registro del lotto e dai risultati verificati; store-and-forward funziona anche se le scuole non sono online contemporaneamente. LoRa non trasporta contenitori biologici.

## Bearer e contratto

- **LoRa:** digest autorizzati di lotto, richiesta, disponibilità e stato `TRIAL_PENDING / OBSERVED / REVIEWED`, rispettando payload realmente disponibile.
- **BLE:** schede sintetiche brevi in prossimità e riconciliazione presso il checkpoint.
- **Wi-Fi/LAN/Internet:** tabelle complete, foto solo di semi/piantine senza persone, documenti metodologici e report.
- **USB/SD/trasporto fisico:** registri verificati e piccoli lotti materiali **solo se consentiti** dalle regole applicabili e dal responsabile scolastico.
- **DISCOVERY:** possibile lotto/esperimento; **EXACT:** ID lotto, versione, hash del registro e delle prove; **SEMANTIC:** compatibilità di specie/varietà/metodo come proposta da verificare, non corrispondenza automatica.

Esempio struttura: `lot_id`, `source_school_coarse`, `species_label`, `approved_distribution_scope`, `inventory_state`, `trial_id`, `sown_count?`, `valid_observations_count?`, `germinated_count?`, `observation_window`, `method_version`, `reviewer_signature?`, `quality=UNKNOWN|PARTIAL|REVIEWED`. Nessun dato personale. Non estrapolare tassi fra protocolli disomogenei.

## Software subito (da implementare)

1. Preparare tre cache e 12 lotti fittizi con quantità/identificatori distinti; iniettare copie duplicate, lotti scambiati, richiesta tardiva, annullamento e consenso negato.
2. Generare esperimenti con date simulate, germinazioni parziali, mancata semina, conteggi contraddittori, dati arrivati fuori ordine, metodo differente e un lotto ritirato.
3. Verificare che `NOT_SOWN`, `NOT_OBSERVED`, `IN_PROGRESS` e `GERMINATED_ZERO_VERIFIED` non siano confusi. Calcolare una proporzione soltanto se denominatore, finestra e protocollo sono esplicitamente validi.
4. Associare ogni risultato al **lotto e trial esatti**; preservare rettifiche e originali, mantenere conflitti aperti fino a revisione; nessun «successo» agronomico sintetico presentato come reale.
5. Confrontare tempo di disponibilità del risultato in simulazione con consegna immediata ideale, distinguendo tempo di osservazione da tempo di ricezione.

**Accettazione:** (A) mai denominatore nullo o ignoto interpretato come 0%; (B) dato di un lotto diverso non modifica il report del lotto richiesto; (C) un ritiro blocca nuove richieste anche se copie vecchie restano in cache una volta recepita la revoca; (D) un conflitto non scompare per ultimo-scrittore; (E) hash completo e verifica del revisore richiesti prima di `REVIEWED`.

## Prova con hardware reale, solo dopo il simulatore

4–6 schede LoRa, due PC e due checkpoint scolastici autorizzati; scambiare inizialmente **solo capsule/lotti fittizi** tra Rometta e Venetico, con relay store-and-forward. Verificare discovery, integrità, ricevute applicative e divergenza/convergenza di due cache. Una successiva prova di germinazione richiede contenitori e protocolli omogenei, approvazione dei docenti, etichette sicure, lotti ammessi, verifiche di eventuali obblighi fitosanitari/commerciali prima di ogni trasferimento effettivo: **mai distribuire semi spontanei, sconosciuti o specie invasive**. Nessuna affermazione su qualità biologica senza osservazioni reali validate.

## Privacy, sicurezza, difficoltà

Non pubblicare nomi, indirizzi, profili di minori o localizzazioni private. Lot-ID non tracciabile fino ai singoli studenti; solo luoghi scolastici autorizzati. Firme/controlli contro la sostituzione di lotto e falsi risultati, permessi di pubblicazione, tempi di conservazione brevi. Gli esperimenti **non certificano** germinabilità commerciale o fitosanitaria. **Medio-alta**: l'algoritmo è fattibile; il protocollo scientifico e la gestione del materiale richiedono supervisione.

## Anti-duplicazione

**UC-043** è marketplace generico di beni; **UC-042** è custodia materiale; **UC-031** è provenienza della calibrazione, **UC-185** gestisce sforzo osservativo, **UC-267/269** parlano di alberi/terreno. **UC-287 non è un altro marketplace:** verifica la **catena lotto → semina → risultato di germinazione → revisione**, con dati mancanti e trasferimento differito di campioni/risultati. Può riutilizzare UC-043/042 senza introdurre nuove primitive radio.
