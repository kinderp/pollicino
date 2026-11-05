# UC-285 — Osservatorio scolastico dei rifiuti spiaggiati con copertura di campionamento esplicita

**Data/stato:** 5 novembre 2026; proposta documentale non implementata, nessuna osservazione ambientale né test fisico. Difficoltà **medio-alta**. PHY LoRa congelato, MAC, driver e firmware invariati.

## Problema

Due scuole si scambiano riepiloghi sui rifiuti visibili in una spiaggia. Se un gruppo ha percorso tutta la sezione e l'altro solo una parte, confrontare «10 oggetti vs 3» come se fossero misure equivalenti sarebbe fuorviante. Ancora peggio: **un sopralluogo mai eseguito non è un sopralluogo con zero rifiuti**. Serve trasferire non soltanto i conteggi, ma anche protocollo di campionamento, porzione osservata, condizioni di validità e revisione.

Lo scenario è **didattico e ambientale**, non una certificazione ecologica né la produzione automatica di dati ufficiali. La metodologia OSPAR su tratti fissi di 100 m è un riferimento metodologico, **non** un'automatica autorizzazione o conformità per spiagge siciliane (altra area geografica).

## Attori, nodi, territorio, perché PollicinoNet

Docenti/scienze, due gruppi di osservatori in aree costiere autorizzate fra Villafranca, Spadafora e Venetico, due checkpoint scolastici, 4–6 relay LoRa studenti volontari, eventuale dispositivo edge che propone categorie e revisore umano. Un ufficio/associazione locale può usare dati aggregati soltanto se autorizzati e verificati.

PollicinoNet trasporta subito piccoli **riepiloghi di sessione con qualità del campione**, mentre moduli completi, foto di dettaglio e schede di controllo arrivano in differita. Un relay che non conosce i dati completi deve poter inoltrare un riferimento senza inventare il numero finale.

## Contratti e bearer

`SurveyRecord={survey_id,site_public_code,protocol_version,section_id,planned_length,observed_length,started_time_interval,ended_time_interval,effort_status,categories_counts,missing_segments[],review_status,exact_evidence_hash,revision_of?,signature}`

Stati distinti: `NOT_SURVEYED`, `IN_PROGRESS`, `INCOMPLETE`, `COMPLETE_PENDING_REVIEW`, `COMPLETE_VERIFIED`, `REJECTED`. Un conteggio **zero** è ammesso solo se la sezione prevista è stata osservata secondo protocollo e la revisione ha convalidato la scheda.

- **LoRa:** ID opachi della sessione, stato di completezza, digest, conteggi compatti per categoria *solo se compatibili con l'adapter*, e segnale di nuova versione.
- **BLE:** sincronizzazione dello smartphone/terminale di osservazione con relay.
- **Wi-Fi/LAN/Internet:** moduli completi, dizionari delle categorie, dati aggregati, foto che non contengano persone riconoscibili.
- **SD/USB/trasporto fisico:** prove e serie storiche fra scuole anche in assenza di backhaul.
- **DISCOVERY:** «nuovo rilievo potenzialmente disponibile»; **EXACT:** protocollo, segmento, stato e versione firmata della scheda; **SEMANTIC:** interpretazione scientifica soltanto dopo revisione delle evidenze.

## Esperimenti immediati in software (non ancora eseguiti)

1. Generare **12 rilievi interamente sintetici** su 3 sezioni, inclusi un rilievo completo con zero, uno saltato per maltempo, tre parziali e uno con conteggi rivisti; seed e ground truth espliciti.
2. Simulare due cache senza Internet e relay intermittenti: ritardi, duplicati, arrivo prima del riepilogo e poi del modulo, correzioni firmate, revoche e versione vecchia che ricompare.
3. Mostrare `COMPLETE_VERIFIED` soltanto se lunghezza/area osservata e revisione sono valide per la **versione di protocollo** dichiarata; per condizioni incoerenti mostrare `INCOMPLETE/UNKNOWN`.
4. Confrontare due metodi di aggregazione: ingenuo che assume «assente=0» e prudente che richiede rilievi completati comparabili; registrare il numero di falsi zeri e di confronti rifiutati.
5. Inserire candidati classificati da edge AI e casi duplicati. La proposta del classificatore non costituisce un conteggio convalidato: revisore umano conferma; non usare foto/facce di persone.
6. Produrre report `SIMULATED` con `PASS/FAIL/UNKNOWN/NOT_TESTED`, seed, numero di survey valide/attese, categoria, revisione ed esatta provenienza. Non estrapolare da un tratto all'intera costa.

**Criteri PASS:** nessuna sessione saltata produce zero; una correzione non crea un doppio conteggio; le repliche ricostruiscono lo stesso insieme di versioni firmate; percentuale di copertura esplicitamente disponibile; differenze fra protocolli non vengono presentate come trend confrontabili.

## Hardware/prove fisiche necessarie

Primo passo in laboratorio: **4–6 schede**, due PC e due gruppi che compilano schede sintetiche mentre un relay trasporta digest/receipt; prova di coerenza delle revisioni ed EXACT. Solo successivamente: un'attività **guidata e autorizzata** su un tratto costiero accessibile e sicuro, dopo aver definito con gli insegnanti campionamento, categorie, permessi e supervisione. Annotare realmente lunghezza e sforzo del rilievo, dispositivi e tempi; un eventuale modello edge deve essere validato contro annotazioni umane. I relay possono trasportare schede tramite incontri opportunistici, senza registrare traiettorie personali. Misurare byte TX/RX e accettazioni applicative effettivi; non inventare copertura o autonomia LoRa.

**Sicurezza in spiaggia:** niente ingresso in acqua, scogli pericolosi o sopralluoghi con condizioni meteo avverse. Nessuna raccolta di rifiuti taglienti, sospetti, sanitari o chimici; non toccarli, segnalare ai responsabili. Non imporre a studenti o minori di rimuovere rifiuti. Niente persone, targhe o indirizzi privati nelle immagini; minimizzare coordinate e custodire i dati di campo secondo policy scolastica.

## Anti-duplicazione

**UC-116** è il citizen-science ferry generale; **UC-185** distingue osservazione negativa e sforzo; **UC-110** elimina duplicati di evidenze visive; **UC-171** riguarda qualità dell'acqua costiera; **UC-273/282** sono edge-AI e confrontabilità fra modelli. **UC-285** introduce uno **schema applicativo e test specifici di copertura del tratto costiero, completezza del sopralluogo, conteggi per categoria e revisioni**, riutilizzando i primitive già documentati. Non è una nuova tecnologia radio.

## Metodo di riferimento

- [OSPAR, Assessment of beach litter 2018–2023](https://oap.ospar.org/en/ospar-assessments/committee-assessments/human-activities/marine-litter/beach-litter-18-23/): sezioni fisse, classificazione per tipologia, attenzione alla confrontabilità; esempio metodologico, non applicazione certificata in Italia.
- [OSPAR, beach litter monitoring](https://www.ospar.org/work-areas/eiha/marine-litter/assessment-of-marine-litter/beach-litter).
