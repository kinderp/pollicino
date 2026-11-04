# UC-281 — Backup P2P offline: ripristinare davvero un servizio entro RTO/RPO

**Stato:** proposta documentale del **4 novembre 2026**; nessuna implementazione o prova eseguita. **Difficoltà:** alta. PHY LoRa congelato, MAC, driver e firmware **non modificati**.

## Problema concreto / user story

Tre laboratori condividono in differita un archivio di progetto Raiatea, un piccolo repository didattico e le relative dipendenze. Una cache conserva byte integri e passa persino gli audit campionari, ma quando il laboratorio deve ripartire manca un indice, una dipendenza o la versione più recente di un file. **Possedere il backup non significa rendere di nuovo utilizzabile il servizio entro la lezione**.

**Come docente** voglio eseguire un ripristino di emergenza **solo simulato** su dati fittizi, valutando separatamente:
- **RPO:** quanto è vecchio l'ultimo stato *consistente* e realmente recuperabile rispetto al momento del guasto;
- **RTO:** quanto dura dal guasto di prova alla disponibilità verificata del servizio completo, **inclusi test di riavvio**.

I target di prova vengono scelti dal docente e sono **ipotesi didattiche, non garanzie operative**.

## Attori e scenario messinese

Un laboratorio sorgente a Messina, un repository/cache presso un checkpoint autorizzato di Rometta, un secondo presso Venetico; 4–6 relay LoRa (anche mobili volontari **senza tracciamento**) per annunci e richieste, due laptop o Raspberry Pi isolati. Il payload del backup è **un dataset sintetico e non identificativo**, mai compiti reali, credenziali, registri o dati degli studenti.

In una prova, il PC del laboratorio perde l'accesso al proprio archivio fittizio; due cache hanno versioni diverse. PollicinoNet trasporta manifest e richieste, mentre i blocchi si recuperano quando un bearer capiente è disponibile. Il gruppo verifica se riesce a lanciare una ricerca Raiatea sintetica o un'app didattica, non soltanto a ricostruire i file.

## Perché PollicinoNet / bearer

La rete può restare partizionata: **DISCOVERY** trova la disponibilità di copie e dipendenze, **EXACT** verifica manifest/blocchi/versioni, **SEMANTIC** individua il servizio didattico desiderato senza essere prova dell'identità dei file.

- **LoRa:** digest/ID di snapshot, piccole richieste di restore, stato di verifica e ricevute *entro i limiti già supportati*; non i backup completi.
- **BLE:** manifest e piccoli blocchi se contatto e adapter lo consentono.
- **Wi-Fi/LAN / Internet:** ricostruzione di file, dipendenze e indici; Internet può essere disabilitato nel braccio offline e usato come controllo nel braccio connesso.
- **SSD/USB e trasporto fisico:** massa dei dati e snapshot fra sedi con custodia verificata; niente esecuzione automatica da supporti esterni.

Evento applicativo (non formato on-air): `{drill_id, service_version, required_manifest_hash, snapshot_time_quality, fault_time, recovery_start, service_ready, latest_consistent_point, evidence_refs, outcome}`. Lo stato `READY` richiede **checksum + dipendenze + smoke test applicativo + policy**; `FILES_PRESENT` non basta.

## Cosa testare subito senza hardware

1. Creare dieci snapshot artificiali di un archivio con file, indice di ricerca, un piccolo servizio e dipendenze, distribuiti su tre cache, con seed e hash EXACT.
2. Iniettare isolamento del laboratorio, un backup mancante, un indice vecchio, blocchi corrotti, versione impossibile da risolvere, ritorno tardivo di un relay e orologi incerti.
3. Simulare due strategie sulle **stesse tracce di contatti**: `recupero a blocchi appena possibile` e `prefetch della chiusura delle dipendenze` (UC-162). Includere un ramo con solo trasporto fisico.
4. Misurare `RPO_osservato = tempo_guasto - tempo_ultimo_snapshot_consistente_recuperato`; `RTO_osservato = tempo_READY_app - tempo_guasto`. Usare una sorgente di tempo simulato comune, o **intervalli d'incertezza**; non produrre RTO/RPO certi da clock non confrontabili.
5. Rifiutare `READY` se manca una dipendenza o il comando di verifica del servizio non passa. `INCONCLUSIVE` quando manca il manifest/clock/ground truth; `FAIL` quando target fissati non sono raggiunti.

**Criteri PASS proposti:** recupero byte-esatto dello snapshot selezionato, manifest e dependency closure completi, servizio risponde allo smoke test, RTO/RPO calcolati separatamente, nessun successo per un backup solo presente o audit campionario passato.

## Gate e prove hardware (non eseguite)

Prima tutto su tre processi/carte di memoria di test. In seguito due laptop/RPi dedicati, 4–6 schede LoRa e due checkpoint scolastici **autorizzati**. Ripetere lo stesso guasto innocuo con LAN disattivata e dati sintetici; registrare la disponibilità effettiva di contatti, il passaggio del manifest su LoRa, i blocchi via Wi-Fi o SSD e l'ora di esecuzione riuscita del test. Confrontare sessioni ripetute e segnare i fallimenti senza ricalibrare i target a posteriori.

**Non disconnettere servizi di produzione, non cancellare backup esistenti e non usare dati personali reali.** Non confondere `COPY_VERIFIED`, `RESTORED` e `SERVICE_READY`; nessuna disponibilità in emergenza viene garantita dalla demo.

## Sicurezza, privacy e limiti

Manifest firmati, cifratura degli oggetti se privati, ACL del destinatario, supporti autorizzati, no esecuzione di script estratti automaticamente, sandbox per lo smoke test, anti-replay e versione del dataset fissata. Anche i nomi delle risorse potrebbero rivelare contenuti: annunciare solo handle autorizzati (UC-278). I relay custodiscono capsule, non credenziali; scadenze e revoche sono riconciliate. Limiti: guasti, alimentazione e throughput reali non sono riproducibili perfettamente in simulazione; i risultati di software e di laboratorio non garantiscono recovery in un disastro.

## Non duplicazione

- **UC-012:** backup e restore opportunistico come funzionalità.
- **UC-091 / UC-036:** integrità/retrievabilità e scrub, non ripartenza del **servizio funzionante** misurata contro un obiettivo.
- **UC-162:** scelta del sottoinsieme di dipendenze, riusata qui come strategia; UC-281 verifica l'intero **tempo al servizio** e il **punto consistente realmente ripristinato**.
- **UC-229 / UC-266:** prontezza di un pacchetto didattico e fairness prima di una scadenza, non ripristino post-guasto e separazione RTO/RPO.
- **UC-253:** persistenza della custodia di un relay, non recovery end-to-end del servizio.

## Riferimento metodologico

- [NIST SP 800-34 Rev. 1, Contingency Planning Guide for Federal Information Systems](https://csrc.nist.gov/pubs/sp/800/34/r1/upd1/final): distingue *Recovery Time Objective* e *Recovery Point Objective* e raccomanda test di ripristino. Il riferimento è metodologico: non costituisce certificazione del testbed PollicinoNet.
