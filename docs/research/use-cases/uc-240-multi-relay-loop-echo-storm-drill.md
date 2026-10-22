# UC-240 — Contenimento di loop ed eco dopo la riunione della rete

**Stato:** proposta documentale del 22 ottobre 2026; non implementata, non misurata. **Difficoltà:** medio-alta.

## Problema e storia d'uso
Nodi A, B e C conservano lo stesso oggetto e lo reinoltrano dopo contatti successivi. Se il grafo dei relay contiene un ciclo (A→B→C→A), partizioni, code recuperate da disco e riavvii possono produrre molte copie inutili. Il problema non è soltanto la duplicazione di un comando all'applicazione: è il consumo cumulativo di memoria e opportunità radio prima dell'accettazione finale.

**Scenario Messina:** sei schede di laboratorio impersonano relay di Messina, Villafranca e Venetico; in una fase successiva due checkpoint scolastici autorizzati scambiano capsule di prova tramite studenti volontari. Non servono itinerari personali o GPS.

## Attori e perché PollicinoNet
Publisher di messaggi sintetici, 4–8 relay store-and-forward, cache/gateway, destinatario e due osservatori di log indipendenti. PollicinoNet è appropriato perché gli oggetti devono sopravvivere a incontri ripetuti e disconnessioni e possono rientrare nello stesso nodo da direzioni diverse. La proprietà da verificare è **contenere il lavoro duplicato senza dichiarare una falsa consegna**; non si promette copertura né una consegna certa.

## Bearer
- **LoRa:** solo annunci/identificativi compatti e un numero strettamente limitato di capsule di test autorizzate; rispettare configurazione e budget radio effettivi.
- **BLE/Wi-Fi:** riconciliazione inventari e payload quando i nodi sono vicini; Internet opzionale per archivio dei log.
- **USB/trasporto fisico:** importazione di copie e replay di uno scenario di disconnessione, con verifica degli hash.

## Esperimento software immediato
Simulatore deterministico di sei nodi con code persistenti, identificativi stabili di oggetto, contatori di inoltro, finestra anti-duplicazione e scadenza; questi sono **meccanismi candidati da studiare**, non caratteristiche dichiarate già presenti nel core. Prove: (1) anello A-B-C-A; (2) due isole poi riunite; (3) riavvio e perdita della cache di elementi visti; (4) copia alterata e hash errato; (5) destinatario offline; (6) oggetto scaduto. Confrontare baseline senza contenimento, limiti locali e riconciliazione differenziale. Criteri di accettazione proposti: nessuna accettazione ripetuta con effetti laterali; numero di inoltri e dimensione delle code **limitati dal budget configurato** in ogni test; gli stati di consegna sconosciuti rimangono sconosciuti. Registrare invii richiesti, invii realmente tentati nel simulatore, copie duplicate, byte utili, code e errori di verifica.

## Prova fisica necessaria
Prima in laboratorio, 6 schede e due ricevitori indipendenti con esperimento **strettamente capped** (mai generare deliberatamente una tempesta radio incontrollata). Poi due checkpoint con relay volontari e carico di prova limitato. Log locali più log ricevitori, orari con incertezza, versione software/configurazione e ricevute applicative. La correttezza del simulatore non dimostra comportamento LoRa: misurare TX/RX reali, contatti, copie, airtime e trasferimenti verificati. Pre-flight di condizioni normative, potenza, antenna e limiti della sottobanda.

## Privacy e sicurezza
Nessuna graduatoria degli studenti né tracciamento di percorsi: ID temporanei, payload inventati, cancellazione dei log alla fine della campagna. Firma/hash e anti-replay per evitare che un avversario inietti copie arbitrarie; limiti per sorgente e ruolo. Un nodo che ha esaurito il budget può rifiutare copie: segnalare le consegne come non confermate.

## Differenza rispetto al catalogo
UC-102 studia groupcast e anti-entropy; UC-175 rende idempotenti gli **effetti applicativi**; UC-108 riguarda la pressione delle code; UC-233 studia il picco di riavvio. **UC-240** isola l'**amplificazione ciclica multi-hop** e il suo contenimento osservabile anche quando i nodi dimenticano parzialmente la storia. Nessuna modifica al PHY LoRa congelato.

Riferimento generale DTN: https://www.rfc-editor.org/rfc/rfc9171.html (non implica conformità BPv7).
