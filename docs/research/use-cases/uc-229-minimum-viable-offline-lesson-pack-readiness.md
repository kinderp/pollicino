# UC-229 — Pacchetto didattico offline verificabile

## Problema e scenario
Un laboratorio riceve file integri ma non può svolgere una lezione per mancanza di compilatore, libreria o dataset. Docente, due laboratori fra Messina e Venetico, PC locali e relay studenti gestiscono la distribuzione.

## Perché PollicinoNet
Store-and-forward consente di recuperare le dipendenze indispensabili in incontri successivi e di portare manifest compatti su LoRa.

## Bearer
LoRa: ID, hash, richieste e stato READY/MISSING. BLE: piccoli oggetti. Wi-Fi/Internet: repository e contenuti. USB/SSD e trasporto fisico: archivi grandi.

## Prova software
Lezione C/Python sintetica con sei componenti obbligatori. Simulare dipendenze mancanti, versione errata, duplicati e manifest vecchio. READY solo dopo verifica hash, licenza e smoke test locale in sandbox.

## Prova fisica
Due PC isolati e 4–6 schede; recuperare i file in fasi e compilare davvero l'esercizio. Misurare completamento e byte effettivi.

## Privacy, sicurezza e difficoltà
Solo materiali autorizzati, nessun voto o dato degli studenti, script di prova controllati, autorizzazioni firmate. Difficoltà media.

## Originalità
UC-029 è una cache di dipendenze, UC-041 un hotspot temporaneo, UC-221 una ricevuta applicativa. UC-229 dimostra la prontezza funzionale della *lezione completa*.
