# UC-292 — Checkpoint LoRa fotovoltaico: autonomia verificabile anche nella stagione sfavorevole

**Stato:** proposta documentale del **8 novembre 2026**; NON implementata, nessun test software e nessuna misura elettrica/radio eseguiti. **Difficoltà: medio-alta.** Il PHY LoRa congelato, MAC, driver e firmware restano invariati.

## Problema concreto

Una scuola dell'area Rometta–Venetico vorrebbe lasciare attivo un **checkpoint fisso** PollicinoNet con alimentazione solare e accumulo, senza connessione elettrica permanente. Una stima basata sul sole estivo o sulla capacità nominale della batteria rischia di sovrastimarne l'autonomia: consumi notturni, perdite del regolatore, periodi nuvolosi, degrado, esposizione locale e limiti dell'accumulatore contano. La domanda verificabile è **per quali condizioni documentate e con quali margini il servizio rimane disponibile**, non «quanti giorni funziona sempre».

**User story:** come docente responsabile di un checkpoint esterno autorizzato, voglio un *gate energetico* che blocchi la dichiarazione di «autonomo» finché profilo di consumo, produzione, stoccaggio e limiti di sicurezza non abbiano evidenze sufficienti.

## Attori, nodi e vantaggio di PollicinoNet

Docente, custode dell'edificio, nodo LoRa fisso, logger elettrico indipendente, regolatore e sistema di accumulo **preassemblati e compatibili**, relay degli studenti, due checkpoint di riferimento (inizialmente simulati), eventuale laboratorio che raccoglie i log. Il relay **store-and-forward** continua a custodire messaggi quando la connettività manca: per questo la continuità energetica del checkpoint è un requisito applicativo indipendente dalla qualità radio.

**DISCOVERY** annuncia soltanto stato grossolano autorizzato del servizio e disponibilità di finestre future; **EXACT** vincola profilo sperimentale, timestamp con incertezza, configurazione, ricevute applicative e report; **SEMANTIC** descrive un bisogno come «checkpoint rurale», senza diventare prova di autonomia.

## Bearer e dimensioni

- **LoRa:** solo piccole capsule/heartbeat consentiti dall'adapter già esistente, identificativi di sessione ed eventi energetici sintetici o osservati in maniera autorizzata; *non* curve ad alta frequenza.
- **BLE:** diagnosi e configurazioni locali solo se già supportate.
- **Wi-Fi/LAN/Internet:** log completi, serie elettriche, dashboard e report quando raggiungibili.
- **USB/SD e trasporto fisico:** backup dei log da checkpoint isolati; i relay volontari trasportano copie senza registrazione degli itinerari.

Nessun comando remoto deve bypassare le protezioni **locali** della batteria o del regolatore. Il servizio deve degradare in modo sicuro quando la riserva è insufficiente.

## Contratto sperimentale proposto

`EnergyRun = {campaign_id, site_class, experiment_epoch, board_profile_hash, adapter_version, radio_config_hash, supply_profile, sampling_interval, load_trace_source, harvest_trace_source, battery_capacity_usable_estimate, temperature_range, controller_losses_model, log_completeness, clock_uncertainty, provenance: SIMULATED|OBSERVED}`.

`EnergyVerdict = {campaign_id, scenario_id, min_service_window, simulated_or_observed_uptime, battery_floor_events, missing_evidence, decision: PASS_TEST_SCENARIO|FAIL_TEST_SCENARIO|UNKNOWN|NOT_TESTED}`.

**Non chiamare 'risultato misurato' un profilo solare esterno o sintetico.** La produzione prevista va distinta da quella effettivamente registrata; una prova breve non certifica l'inverno. Non usare RSSI/PDR presunti come evidenza energetica.

## Prova software immediata, senza schede

1. Generare (seed fisso) **30 giorni simulati** di luce variabile e consumo separato in idle, RX, TX, elaborazione e riavvio; introdurre tre sequenze di giornate nuvolose e due log incompleti. Input in Wh/ora e specifica delle assunzioni.
2. Implementare bilancio a intervalli con rendimento di carica/scarica, energia utilizzabile, soglia di arresto e carico di servizio: nessuna energia può nascere dal modello; stato energetico sempre nel range dichiarato.
3. Confrontare due politiche applicative: checkpoint sempre attivo e **servizio a finestre pubblicate** quando la riserva è bassa. La seconda non deve promettere consegne mentre è spento.
4. Calcolare disponibilità simulata, energia spesa per *capsula accettata* (solo quando il modello esplicita tale accettazione), messaggi in coda, downtime, profondità di scarica, margine e intervalli **UNKNOWN** per dati mancanti.
5. Variare capacità nominale vs usabile e rendimenti; impedire verdetti favorevoli quando le misure necessarie mancano.

**Accettazione software:** (A) nessuna violazione delle soglie locali; (B) dimensioni e unità coerenti; (C) nessuna generalizzazione stagionale da un solo giorno; (D) sessioni riproducibili con seed/fixture; (E) report sempre marcati `SIMULATED` e `PASS/FAIL/UNKNOWN/NOT_TESTED`. **Non eseguiti**.

## Prove fisiche da autorizzare, non svolte

Prima in laboratorio: un nodo LoRa, due nodi di riferimento, alimentazione a **bassa tensione**, sistema commerciale sicuro per pannello/accumulo, logger V/I/energia indipendente e supervisione. Misurare più cicli di carico e una giornata di servizio; confrontare consumo registrato e ricevute `app_accepted`. Poi **una stazione fissa** in proprietà scolastica autorizzata, non su tetti o pali accessibili ai minori, con monitoraggio protratto e manutenzione; non dichiarare autonomia stagionale finché la serie copre condizioni sfavorevoli o non è validata da un modello con margini espliciti.

Verificare autorizzazione installativa, esposizione, rischio incendio/umidità e requisiti elettrici; niente assemblaggio di pacchi batteria, modifiche a celle o collegamenti alla rete 230 V. Verificare limiti radio applicabili (frequenza, potenza, duty cycle) prima di trasmettere.

## Privacy, sicurezza, limiti e anti-duplicazione

Niente indirizzi di case, orari di passaggio, identificativi permanenti o performance individuali degli studenti nei report; stato energetico grossolano pubblicato solo a nodi autorizzati perché può rivelare presenze o infrastrutture. Adottare identificativi di campagna e cancellazione programmata di log.

**Non è UC-052** (coordinazione di carichi flessibili tra isole energetiche): qui si verifica la **fattibilità continuativa di alimentare un unico checkpoint**. **Non è UC-252** (giornata di un relay volontario), **UC-271** (alimentazione e RF), **UC-289** (autoshutdown USB), **UC-286** (recupero dopo boot) o **UC-214** (salute della custodia esterna). Il risultato principale è un *gate di autonomia del servizio con incertezza*, non la strategia di coordinamento o la durata nominale.

**Fonti per impostare, non certificare, il modello:** [NREL PVWatts](https://pvwatts.nrel.gov/) (stima della produzione fotovoltaica, non misura della specifica installazione); [ETSI EN 300 220-2](https://portal.etsi.org/) (verificare la versione e l'applicabilità normativa alla configurazione reale).
