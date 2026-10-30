# UC-266 — Equità della disponibilità dei materiali didattici offline

**Stato:** proposta del 30 ottobre 2026, nessuna misura di accesso o consegna raccolta. PHY LoRa congelato invariato.

## Problema risolto

Un pacchetto didattico può essere integro e utilizzabile nel laboratorio principale ma **arrivare troppo tardi agli altri checkpoint**. Se misuriamo solo il numero totale delle copie, potremmo non accorgerci che un gruppo riceve spesso gli aggiornamenti dopo l'inizio della lezione. Il problema non è valutare gli studenti: è verificare l'equità operativa del **servizio di distribuzione** fra sedi e decidere se usare un'alternativa prima di una scadenza didattica.

## Attori e scenario Messina

Docente/editore, cache di scuola, due o tre PC di checkpoint autorizzati (ad esempio Messina, Rometta, Venetico), 4–8 relay store-and-forward volontari e verificatore di pacchetti. Le sedi rappresentano punti di prova, non abitazioni né studenti individuali. Materiale: un kit C/Python senza dati personali e autorizzato alla redistribuzione.

## Perché PollicinoNet e trasporti

Lo store-and-forward accetta consegne tardive, ma deve misurare esplicitamente **`READY_BEFORE_DEADLINE`**, `READY_LATE`, `INCOMPLETE` e `UNKNOWN`, distinguendo disponibilità dei contenuti da sola presenza del file in rete.

- **LoRa:** annuncio dell'ID/versione/hash del kit, richieste di componenti mancanti e stato compatto.
- **BLE:** scambio locale di manifest o piccoli file.
- **Wi-Fi / Internet:** trasferimento dei pacchetti didattici completi e sincronizzazione facoltativa.
- **USB/SD/trasporto fisico:** recupero offline di materiale voluminoso attraverso persone che già effettuano spostamenti ordinari.
- `DISCOVERY`: versione/need; `EXACT`: manifest, dipendenze, hash, log di prontezza con tempo e incertezza; `SEMANTIC`: etichette di fruibilità della lezione.

## Test software immediato

Generare un kit con manifest, dipendenze eseguibili e scadenza; emulare tre cache con bande e finestre di contatto differenti e 8 relay virtuali. Iniettare disponibilità solo dell'hash, pacchetto completo ma versioni errate, file mancanti, malware fittizio bloccato, ricevuta applicativa senza prova di eseguibilità, clock incerto, duplicati e messaggi fuori ordine. Confrontare FIFO, replica preventiva controllata e recupero mirato dei soli file mancanti, **con uguale budget simulato**.

Misure: quota di checkpoint effettivamente `READY` alla scadenza, ritardo rispetto all'orario didattico, byte utili, quantità di dati mancanti, costo per sede, intervallo di incertezza quando log/clock non sono sufficienti. Evitare metriche di equità su gruppi troppo piccoli o che identifichino persone. Una `READY` tardiva non viene retrodatata.

## Prova con hardware reale

Due PC scollegati dalla rete e 4–6 schede in laboratorio: distribuzione dell'annuncio LoRa, passaggio manifest via BLE, kit via Wi-Fi oppure USB, controllo degli hash e *smoke test* in sandbox. Successivamente tre checkpoint di scuola autorizzati e relay portati volontariamente negli spostamenti ordinari. Raccogliere TX/RX, evidenza di trasporto/accettazione, tempi con incertezza e costo fisico dei vari bearer. Niente affermazioni sulla copertura provinciale senza campagna di misura.

## Privacy e sicurezza

Nessun registro di connessione dei singoli alunni, voti, profili didattici, ubicazioni domestiche o tragitti. Report **solo per checkpoint istituzionale**, con eventuale aggregazione/soppressione di numeri piccoli; consenso dei volontari e arresto locale. Manifest firmati, permessi di redistribuzione, versioni e licenze verificati; script didattici eseguiti soltanto in sandbox. Nessuna lista di scuole/utenti "peggiori" dedotta da esposizioni sperimentali non comparabili.

**Difficoltà:** media per la simulazione, medio-alta per il test distribuito e la correttezza statistica.

## Originalità rispetto al catalogo

UC-041 offre hotspot didattici; UC-095 regola l'equità delle risorse dei relay; UC-098 lega le ricevute; UC-228 controlla il bias da connettività; UC-229 stabilisce la **prontezza tecnica di un singolo kit**; UC-241 distribuisce i mazzi di ripasso. **UC-266 valuta invece se ogni checkpoint abbia materialmente un kit funzionante *prima della scadenza comune*, con incertezza e alternative**, non solo se un pacchetto sia integro o una coda sia equamente servita.

## Gate di accettazione (da implementare)

- Un checkpoint non passa a `READY` finché hash, dipendenze, licenza e prova funzionale del kit non risultano validi.
- I ritardi dei relay non trasformano `READY_LATE` in `READY_BEFORE_DEADLINE`.
- Mancanza di log o orologi incoerenti producono `UNKNOWN` con motivazione.
- Le analisi non contengono ID di studenti né percorsi.
