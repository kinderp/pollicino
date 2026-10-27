# UC-257 — Risposta privata una tantum a un annuncio GeoTopic offline

**Stato:** proposta del 27 ottobre 2026; nessun software realizzato e nessuna misura sul campo. **Difficoltà:** alta (privacy, autorizzazione e gestione degli abusi).

## Problema e storia concreta

Nel topic pubblico di un laboratorio scolastico una persona pubblica: «Cerchiamo un sensore da prestare per l'esperimento». Chi possiede il sensore vorrebbe rispondere privatamente, senza pubblicare il proprio contatto personale, il tragitto seguito dal relay o il proprio profilo in tutte le cache territoriali. Non è garantita alcuna connessione end-to-end.

**User story:** come partecipante autorizzato a una stanza GeoTopic voglio rispondere a un annuncio mediante un canale privato circoscritto a quell'annuncio, anche in differita; il publisher deve poter chiudere la possibilità di risposta e impedire duplicati, spam e abuso della funzionalità.

Il sistema non promette anonimato assoluto o assenza di analisi del traffico. Fornisce **minimizzazione dei dati e capacità di risposta limitata**, non una prova della posizione o un nuovo social network.

## Attori / nodi e esempio Messina

- Publisher di un annuncio in una stanza pubblica approvata (per esempio un laboratorio di Rometta).
- Rispondente volontario (per esempio un laboratorio di Venetico), con client locale.
- Cache della stanza e nodo mailbox dell'autore; relay studenti store-and-forward fra checkpoint scolastici autorizzati.
- Moderatore/gestore delle ammissioni, eventuale gateway Internet: non necessario per la consegna differita.

L'oggetto pubblico contiene solo un riferimento all'annuncio e un **reply descriptor a scadenza**, non un indirizzo personale. Il rispondente genera una busta cifrata al destinatario prevista dal descriptor e la invia verso una mailbox pseudonima. L'identità reale non deve essere necessaria ai relay. Il destinatario può ritirare o far scadere il descriptor; i vecchi messaggi già partiti potrebbero comunque arrivare e vanno trattati come scaduti/non ammessi se la policy lo prevede.

## Perché PollicinoNet

- **DISCOVERY:** breve ID dell'annuncio e disponibilità di un canale di risposta, senza nomi personali.
- **EXACT:** hash del descriptor, versione/expiry, riferimento all'annuncio, mailbox pseudonima, nonce, limiti di uso, firma autorizzata e ricevuta applicativa.
- **SEMANTIC:** DNA può suggerire una corrispondenza fra domanda/offerta, ma non attribuisce una relazione personale o garantisce disponibilità del materiale. Il matching è distinto dall'autorizzazione a rispondere.

Una **capability** di risposta è legata a stanza, annuncio, ambito, periodo e destinatario. «Una tantum» significa che una singola capability non deve provocare più di una accettazione logica nello stesso dominio di custodia/validazione: in presenza di nodi che prendono decisioni indipendenti durante partizioni, una garanzia globale di utilizzo singolo *non* è possibile senza coordinamento o una successiva riconciliazione. Il prototipo deve mostrare questa limitazione, non nasconderla.

## Bearer

- **LoRa:** solo hint opachi, digesti, richieste/ricevute di dimensione realmente ammissibile; il testo cifrato soltanto se sta nei limiti misurati.
- **BLE:** scambio locale di mailbox/inventari e buste compatte.
- **Wi-Fi/LAN/Internet:** contenuti e allegati, se disponibili.
- **Trasporto fisico (USB/SD, portatile):** buste cifrate, controllate da hash e autorizzazioni.

## Cosa testare ora senza hardware

Due client e tre cache Python simulati; due stanze e un relay con consegna differita. Testare:

1. Un annuncio valido produce un descriptor firmato legato al corretto room_id e post_id.
2. Una risposta in una stanza diversa, oltre il limite, firmata da autorità sbagliata o con descriptor scaduto è rifiutata.
3. Inoltri duplicati, riordini e riavvii danno un'unica accettazione logica **presso il destinatario**, non duplicati nel thread.
4. Un autore ritira il canale mentre è offline: i nodi in ritardo espongono correttamente lo stato di revoca sconosciuto e non promettono revoca istantanea.
5. Con due cache separate, la stessa capability può essere presentata in entrambe: si rileva il conflitto e si riconcilia, senza affermare un'irrealistica single-use globale.
6. Un relay non dispone di chiavi per leggere le risposte; i log e l'interfaccia non mostrano indirizzi, nomi o percorso dello studente.
7. Un attaccante simulato invia molte risposte: quota, moderazione e costo di ammissione limitano la pressione senza bloccare indiscriminatamente messaggi validi.
8. Una risposta applicativa viene accettata/rifiutata con receipt distinta dalla semplice consegna (UC-221).

Misurare rifiuti corretti, duplicati accettati, visibilità delle revoche, byte per bearer, numero di campi identificativi esposti e ritardi simulati. Niente dati di persone reali nel dataset di sviluppo.

## Prove fisiche

Due PC (publisher e rispondente), un terzo nodo mailbox, 4–6 schede LoRa e checkpoint controllati. In una prima demo in laboratorio, isolare i PC e trasportare un hint di risposta attraverso una scheda spenta/riaccesa fra due incontri. Poi, se autorizzato, due checkpoint scolastici fra Rometta e Venetico con relay volontari. Registrare le effettive ricezioni, le ricevute di validazione, gli scaduti, i byte trasportati e i tempi. Allegati esclusivamente tramite Wi-Fi/USB autorizzati; non assumere copertura o latenza locale prima delle misure.

## Privacy, sicurezza e limiti

Cifratura end-to-end delle risposte; chiavi effimere ove pratico, scope e TTL brevi, anti-replay persistente, rate limit, moderazione per contenuti pubblici, nessun telefono/mail/GPS obbligatorio. Un relay potrebbe dedurre metadati di timing o dimensione: collegare l'audit di linkabilità UC-189 e non dichiarare anonimato forte. Partecipazione volontaria dei minori solo in attività autorizzate; usare account e contenuti fittizi nella demo. Evitare scambi economici o beni fisici non supervisionati.

## Perché non è un duplicato

**UC-023** è una mailbox privata verso un destinatario noto/pseudonimo; **UC-236/247/250** definiscono stanze, vita e namespace; **UC-239** modera post pubblici; **UC-251** identifica bisogni senza inventare offerte; **UC-026** definisce ticket per azioni offline. **UC-257** risolve l'incontro fra un annuncio *pubblico* e una risposta *privata* autorizzata per quel singolo post, senza diffondere i contatti dell'autore. Il risultato è una user story FSL distinta.

Nessun cambiamento al PHY LoRa, MAC, driver o firmware radio.
