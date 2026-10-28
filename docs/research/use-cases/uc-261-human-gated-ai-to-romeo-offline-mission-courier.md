# UC-261 — Dall'AI a Romeo: missione differita proposta, validata e approvata da una persona

**Stato:** caso d'uso documentato il 28 ottobre 2026, non implementato e senza prove fisiche. **Difficoltà:** alta; valutazione della sicurezza fisica obbligatoria prima dell'uso del robot.

## Problema concreto

Un assistente AI suggerisce «fai controllare a Romeo due punti del banco di prova e riporta i risultati». Se il robot è scollegato, la proposta può arrivare molte ore dopo, quando l'area di test, l'hardware o il compito sono cambiati. Un LLM può inoltre produrre parametri errati o non previsti. **Non deve mai bastare ricevere un testo generato per muovere il robot.**

**User story:** come docente o studente supervisore voglio usare un agente AI per **proporre** un piccolo compito strutturato; un validatore deterministico e un'approvazione umana devono autorizzare l'esatta missione, che Romeo esegue soltanto in uno spazio controllato e in una finestra di validità. I risultati arrivano come evidenze differite.

## Attori, nodi e confine di fiducia

Assistente AI o client di pianificazione (**non attendibile per l'esecuzione**); compilatore verso DSL/JSON limitato; validatore locale; docente/supervisore autorizzato; mailbox missioni; relay PollicinoNet; Romeo con controller e arresto locale indipendente; collezionista dei risultati.

Stati: `AI_PROPOSAL` → `SCHEMA_VALID` → `HUMAN_APPROVED` → `QUEUED` → `LOCAL_SAFETY_CHECK` → `EXECUTED` oppure `REJECTED/EXPIRED/ABORTED`. Nessun salto di stato per semplice ricezione radio. L'AI non firma approvazioni umane.

Una missione limitata comprende `mission_id`, `hardware_profile_hash`, `allowed_actions[]`, `max_duration`, `speed_limit`, `test_area_id`, `approval_signature`, `expiry`, `command_epoch`, `idempotency_key`, `expected_evidence`. Le autorizzazioni sono vincolate alla **versione esatta del piano**, del profilo robot e del contesto di test; modifiche successive richiedono nuova approvazione.

## Perché PollicinoNet e bearer

La rete separa preparazione, approvazione, recapito ed esecuzione senza collegamento continuo. **LoRa** può annunciare ID/digest della missione e riportare ricevute/risultati compatti entro limiti verificati, ma **non deve veicolare il controllo motorio in tempo reale**. **BLE/Wi-Fi/LAN** sincronizzano piani e log quando Romeo è vicino; **Internet** facoltativo; **USB/SD o trasporto fisico** per allegati, log e modelli. `DISCOVERY` del piano non equivale al contenuto `EXACT` firmato da validare.

## Software testabile subito

Con un robot simulato e due PC isolati, generare piani JSON sintetici senza dipendere da un LLM. Un mock dell'agente produce anche input ostili o malformati.

1. Una missione conforme ma **non firmata da un umano autorizzato** non può produrre un comando di movimento.
2. Rifiutare azioni non previste, velocità/durate oltre soglia, profilo hardware diverso, firma/epoch errata e missione scaduta.
3. L'ordine dei messaggi viene invertito: l'approvazione prima o dopo il piano non deve consentire di eseguire un piano diverso da quello firmato.
4. Iniettare reboot, duplicati, replay e due cache che consegnano lo stesso piano: al massimo una esecuzione logica per `idempotency_key` presso il controller del robot.
5. Il messaggio dell'agente contiene «ignora il limite di velocità»: il parser non deve interpretarlo come istruzione autorizzata.
6. Il supervisore annulla la missione mentre una cache è isolata: in assenza di prova attuale di autorizzazione locale, il controller adotta la politica conservativa documentata. La revoca non è istantanea attraverso partizioni.
7. L'esito `EXECUTED` richiede evidenza del controller locale; `DELIVERED` e `ACCEPTED` non lo implicano (UC-221).

**PASS software:** zero movimenti simulati da piani non approvati o invalidi; nessuna doppia esecuzione per replay nel dominio del robot; rifiuto esplicito di scadenze e profili errati; log con hash e versioni. Non è una certificazione di sicurezza robotica.

## Prova con hardware

Prima eseguire in simulazione. Solo poi testare **Romeo su banco delimitato**, sotto supervisione di un adulto, con velocità/escursione minime, protezioni delle parti mobili, arresto locale facilmente raggiungibile e nessun movimento se il collegamento d'emergenza locale è indisponibile. Il controllo di arresto non dipende da LoRa, dal gateway o dall'LLM. Due PC, 4 schede LoRa per store-and-forward e Romeo con i suoi componenti già disponibili; evitare test non supervisionati, spazi pubblici, veicoli reali o droni. Misurare recapito piano, latenza di validazione, rifiuti, risultati e duplicati; nessuna autonomia radio o affidabilità motoria presunta.

## Privacy, sicurezza e anti-duplicazione

Usare identificativi fittizi e piani senza video, volti, indirizzi o percorsi individuali. Cifrare i contenuti ove opportuno, autenticare i revisori, mantenere attestazioni di versione, finestra di validità e anti-replay persistente; log limitati nel tempo. Non fare test di incidenti reali, soccorso o protezione civile.

**Non duplicato:** UC-010 è una mailbox generica del robot, UC-026 un ticket autorizzativo, UC-133 controlla l'epoch, UC-175 l'idempotenza, UC-198 l'attuazione scaduta, UC-243 i risultati di tornei. **UC-261 integra il confine AI non attendibile → piano dichiarativo → validazione deterministica → approvazione umana → esecuzione differita controllata**, senza assimilare il testo del modello a un comando. Nessuna modifica PHY/MAC/driver/firmware.
