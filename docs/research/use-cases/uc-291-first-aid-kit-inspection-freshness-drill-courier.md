# UC-291 — Ispezioni dei kit di primo soccorso: «pronto» solo con verifica recente (esercitazione)

**Stato:** nuova proposta documentale del **7 novembre 2026**, non implementata. **Solo dati fittizi e prove di addestramento, non servizio di emergenza.** Nessun test/esperimento fisico eseguito; **difficoltà alta** per responsabilità, autorizzazioni e aggiornamento degli stati. Nessuna modifica a PHY LoRa congelato, MAC, driver o firmware.

## Problema concreto

Durante un'esercitazione scolastica una bacheca offline segnala «kit disponibile» perché ha ricevuto un inventario giorni prima. Nel frattempo un ispettore autorizzato ha segnato una scadenza, un sigillo mancante o uno spostamento. La bacheca non deve mostrare `READY` soltanto perché esiste un vecchio messaggio positivo; **inventario, ispezione fisica, scadenza e stato corrente sono cose diverse**.

**Scenario Messina:** tre sedi/aule scolastiche autorizzate fra Messina, Villafranca, Rometta e Venetico partecipano a una simulazione con tre kit *fittizi*, un registro di verifica e due checkpoint. Capsule di esercitazione percorrono relay store-and-forward volontari. Nessuna diffusione pubblica come se fosse un'informazione ufficiale di protezione civile o soccorso.

## Attori e valore per PollicinoNet

Responsabile scolastico designato, ispettore **autorizzato**, referente esercitazione, checkpoint con cache, relay studenti volontari che vedono soltanto identificativi opachi, bacheca dimostrativa. PollicinoNet può riconciliare eventi **verificati, ritardati o contraddittori** anche con Internet assente. La rete **non certifica** l'idoneità delle attrezzature e non sostituisce un inventario o un'ispezione obbligatoria.

## Bearer, dati e stati

- **LoRa:** micro-eventi firmati di simulazione (`CHECK_AVAILABLE`, `STATUS_CHANGED`, digest), solo se compatibili con adapter già presenti.
- **BLE:** lettura locale degli stati simulati e accesso per personale abilitato, se supportato.
- **Wi-Fi/Internet:** checklist, firmatari autorizzati, allegati e revisioni.
- **SD/USB/trasporto fisico:** trasporto di checklist e report di esercitazione fra sedi offline.
- **DISCOVERY** annuncia una nuova attestazione; **EXACT** identifica la versione autentica e autorizzata; **SEMANTIC** decide unicamente lo stato *nell'esercitazione*.

Contratto: `KitInspection={campaign_id, kit_pseudonym, location_public_site_code, check_id, observed_at_interval, recorded_at, inspector_role, checklist_version, inspection_status, defects[], validity_until?, supersedes?, signature, authorization_epoch, evidence_hash, source=SIMULATED}`.

Distinguere `NEVER_INSPECTED`, `INSPECTED_VALID_IN_DRILL`, `EXPIRED`, `DEFECT_REPORTED`, `STATUS_CONFLICT`, `UNKNOWN_OFFLINE`, `REVIEW_REQUIRED`. Un evento `PLANNED` non equivale a `DONE`; l'assenza di una segnalazione non equivale a verificata disponibilità.

## Prove in software subito — non eseguite

1. Simulare **12 kit fittizi** e due sedi scolastiche più un collector, con check validi, scadenze trascorse, check pianificati non svolti, doppie firme, cambi di versione checklist e una revoca.
2. Replicare gli eventi attraverso tre cache con connessioni intermittenti: un vecchio `READY` arriva *dopo* un rapporto di difetto e una firma non autorizzata arriva prima di quella valida.
3. La bacheca di prova deve distinguere ultimo **messaggio ricevuto** da ultimo **stato attendibile e attuale**, gestire orologi incerti e rifiutare conclusioni certe quando mancano autorizzazioni o verifiche.
4. Testare fallback: con stato scaduto o contraddittorio mostrare `UNKNOWN/REVIEW_REQUIRED` senza inventare il possesso fisico del kit e senza cancellare gli eventi pregressi.
5. Report deterministico `PASS/FAIL/UNKNOWN/NOT_TESTED` con `source=SIMULATED` e tempo/epoch per ogni decisione.

**Criteri PASS:** (A) un evento pianificato non abilita `READY`; (B) difetti autentici successivi non sono sovrascritti da copie ritardate precedenti; (C) firma/ruolo non autorizzati non attestano verifica; (D) stato `UNKNOWN` non è presentato come pronto; (E) vista operativa e audit conservano la distinzione fra ispezione e mera consegna del messaggio.

## Hardware e verifica umana

Fase iniziale: **4–6 schede**, 2 PC e checklist di **kit volutamente simulati**, senza alcun dispositivo medico vero. Misurare solo consegna, età dello stato e ricevute applicative; l'esperimento non prova disponibilità in situazioni reali. Qualsiasi eventuale estensione a dotazioni reali richiede autorizzazione della direzione e personale competente, procedura ufficiale e controllo fisico indipendente dal software. **Mai sostituire le procedure di pronto soccorso o protezione civile con la rete sperimentale.**

## Privacy, sicurezza e non-duplicazione

Niente informazioni sanitarie o nominativi; ID fittizi, firme e ruoli autorizzati, revoche e timeout, log a scadenza, nessuna geolocalizzazione individuale degli studenti. Nessun allarme reale, nessun consiglio clinico, divieto di dichiarare `READY` a utenti finali fuori dal contesto etichettato **ESERCITAZIONE**.

**UC-015** tratta inventari generici; **UC-089** tratta allarmi e acknowledgement; **UC-200** l'after-action di esercitazioni; **UC-132** aggiornamenti di allerte; **UC-267** un diario per alberi. **UC-291** verifica **l'attualità e l'autorità di un'ispezione fisica periodica con scadenze e segnalazioni difetto**, separando lo stato della dotazione dalla semplice presenza di un messaggio offline. Riuso dei contratti di autenticazione, temporalità e revoca già documentati; nessuna nuova promessa radio.
