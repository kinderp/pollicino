# UC-246 — Confine di fiducia per documenti Raiatea in RAG offline

**Stato:** proposta documentale 23 ottobre 2026, integrata nel catalogo il 24 ottobre. Non implementata né certificata sicura. **Difficoltà:** alta.

## Problema e attori
Una scuola riceve via P2P un documento Raiatea integro e firmato. Il testo però contiene istruzioni dirette all'assistente AI, ad esempio ignorare le fonti o richiamare strumenti non autorizzati. La firma conferma origine e integrità del **documento**, non gli conferisce autorità di impartire comandi. Attori: docente editore, revisore, indicizzatore Raiatea, motore RAG, due PC isolati, cache e 4–6 relay PollicinoNet.

## Perché PollicinoNet
Documenti, versioni e revisioni arrivano in ordine variabile e con ritardo. PollicinoNet trasferisce oggetti e metadati; Raiatea li indicizza; l'applicazione RAG deve mantenere il **confine fra contenuto recuperato non attendibile e istruzioni autorizzate**. Il relay non interpreta il testo.

## Bearer
- **LoRa:** piccoli identificativi, stati e avvisi di revisione; non corpi documentali.
- **BLE / Wi-Fi / Internet:** scambio di manifest completi, documenti e indici.
- **USB / trasporto fisico:** corpus e modelli di grandi dimensioni, sempre verificando integrità e provenienza.

## Contratto e lifecycle
Oggetto con hash completo, versione del parser, policy, licenza, visibilità, provenienza e stato `PENDING` / `QUARANTINED` / `REVIEWED` / `REJECTED`. La risposta cita l'esatta versione di ogni documento effettivamente consultato. La quarantena è una decisione applicativa, non un segnale sufficiente che ogni documento approvato sia privo di attacchi.

## Test subito senza schede
Due laboratori virtuali, un corpus fittizio e un set benigno di istruzioni avversarie inserite nei documenti, senza dati reali. Testare riordino, revoche tardive, falsi riferimenti, citazioni inesistenti, prompt injection e duplicati. Un harness controlla citazioni esistenti, tool non invocati su richiesta di testi recuperati, nessuna divulgazione di segreti fittizi, versioni usate ed esiti di verifica. Registrare falsi positivi e attacchi riusciti nel set di prova: nessun filtro garantisce invulnerabilità.

## Prove fisiche
4–6 schede e due PC, prima in laboratorio, poi checkpoint scolastici autorizzati. LoRa porta piccoli stati/ID, Wi-Fi o USB i file. Misurare TX/RX effettivi, ordine di arrivo, latenza della quarantena, distribuzione del verdetto e reale accettazione applicativa; nessun dato disponibile oggi.

## Privacy e sicurezza
Niente credenziali, registri scolastici o dati personali. Sandbox con privilegi minimi, policy di tool use esterna ai documenti, autenticazione del revisore, audit log minimo. Una revoca non raggiunge immediatamente le cache offline: non promettere cancellazione istantanea.

## Anti-duplicati
UC-046 riguarda risposte con fonti; UC-099 l'indicizzazione; UC-186 le contraddizioni; UC-225 il poisoning dei dataset; UC-239 la moderazione dei contenuti. **UC-246 verifica la separazione fra testo RAG non attendibile e istruzioni eseguibili**.

Riferimento: [OWASP LLM Top 10 / Prompt Injection](https://owasp.org/www-project-top-10-for-large-language-model-applications/).
