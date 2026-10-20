# UC-235 — Staffetta cooperativa di enigmi tra scuole disconnesse

**Stato:** proposta documentale del 20 ottobre 2026; demo non ancora realizzata.

## Problema
Come offrire agli studenti una dimostrazione concreta di PollicinoNet oltre ai grafici delle prestazioni radio? Due gruppi devono completare una serie di enigmi cooperativi, ma conferme e suggerimenti possono arrivare fuori ordine e ore dopo. Si deve evitare che duplicati facciano contare due volte la stessa soluzione.

## Attori e scenario Messina
Docente che prepara tre sfide, squadre con pseudonimo in due laboratori (per esempio Messina e Venetico), due computer e 6–10 schede LoRa volontarie come relay. Le azioni avvengono ai checkpoint scolastici, non lungo percorsi personali.

## Perché PollicinoNet; bearer
LoRa trasporta token compatti: ID della sfida, hash della versione, prova di completamento, ricevuta e riferimenti. BLE/Wi-Fi distribuiscono pacchetti di contenuti; Internet è opzionale; USB/QR può essere un altro bearer. Store-and-forward permette a ogni gruppo di proseguire localmente e sincronizzarsi più tardi.

## Test software immediato
Due server Python isolati e otto relay simulati. Preparare tre sfide con dipendenze esplicite; iniettare messaggi ritardati, duplicati, soluzioni concorrenti, replay e contenuti di versioni precedenti. Stati minimi: `PENDING`, `ACCEPTED`, `REJECTED`, `UNKNOWN`. Verificare accettazione al massimo una volta per coppia squadra/sfida/versione e riconciliazione deterministica.

## Prova fisica necessaria
Due PC e 6–10 schede in due laboratori, oppure inizialmente due aule dello stesso istituto. Misurare davvero consegne, ricevute, tempi e duplicati soppressi; poi valutare incontri opportunistici fra checkpoint autorizzati. Nessun dato di copertura presunto.

## Privacy, sicurezza, difficoltà
Squadre pseudonime, niente tracciamento o classifica nominativa, prove di completamento autenticate e segreto delle soluzioni conservato ai capi del gioco. Difficoltà **media**. Output FSL: demo locale, test automatizzati e documentazione di stati convergenti. PHY invariato.

## Originalità
UC-023 è messaggistica privata, UC-028 è collaborazione su note, UC-051 è voto e UC-054 è consegna di elaborati. **UC-235 è un'applicazione cooperativa a eventi e dipendenze, con verifica differita**, facilmente dimostrabile dagli studenti.
