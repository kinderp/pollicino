# UC-248 — Rilevanza contestuale delle notifiche, calcolata sul dispositivo

**Stato:** proposta del 24 ottobre 2026, non implementata. **Difficoltà:** medio-alta (policy, contesto incompleto, privacy).

## Problema concreto
Una room GeoTopic pubblica annunci che hanno senso solo per alcuni partecipanti. Chi segue `robotica` e si trova presso un checkpoint scolastico non dovrebbe ricevere notifiche sul cinema; chi si interessa al cinema potrebbe volerle ricevere solo nell'intervallo di apertura. Se il profilo personale viene trasmesso a tutti i relay, il servizio diventa uno strumento di profilazione.

## Attori e nodi
Editori delle room (UC-236, UC-247), client locali di studenti/docenti, relay negli zaini, cache di scuola, supervisore di privacy. Sperimentazione iniziale fra due laboratori virtuali, poi nodi autorizzati a Messina, Villafranca e Venetico.

## Perché PollicinoNet
Un relay può trasportare **annunci pubblici minimizzati e versionati** senza conoscere il profilo del destinatario. Il client finale valuta localmente rilevanza e autorizzazione: la sottoscrizione semantica rimane distinta dalla distribuzione DTN. Le notifiche arrivate tardi devono essere riconsiderate usando validità e freschezza, non mostrate automaticamente.

## Dimensioni di contesto dimostrative
Zona pubblica, topic, tempo/freschezza, interesse/intenzione dichiarata, capacità/preferenze del dispositivo, visibilità/autorizzazione. Sono una **proposta di profilo applicativo** da confrontare con il modello DNA, non una tassonomia già approvata delle dimensioni del contesto.

## Bearer
- **LoRa:** solo annuncio ridotto (ID opaco, topic grossolano se pubblicabile, area pubblica, scadenza).
- **BLE:** ricezione locale di annunci autorizzati.
- **Wi-Fi / Internet:** contenuti completi e policy versionate.
- **USB / trasporto fisico:** pacchetti di room pubbliche prevalidati per isole offline.

## Contratto e test software immediati
Regole `match` con `policy_version`, `content_visibility`, `topic`, `coarse_zone`, `valid_from/until`, `confidence` se derivata; output `ELIGIBLE`, `HIDDEN`, `EXPIRED`, `UNKNOWN`. Simulare 100 annunci, 10 profili fittizi, profili assenti, autorizzazione revocata, orologi imprecisi, stanze sovrapposte, riordino e duplicati. `UNKNOWN` per dati mancanti, mai assumere autorizzazione. Test di non-divulgazione: nessun profilo/coordinate personali nei bundle e nei log del relay. Misurare precisione e richiamo **solo** contro etichette sintetiche esplicite; non inferire veri interessi degli studenti.

## Hardware reale
4–8 schede per pubblicare eventi sintetici in 2–3 zone scolastiche, 2 telefoni/PC per valutazione locale. Misurare latenza dalla ricezione alla decisione, quantità di annunci trasferiti e differenza fra apparente contatto e messaggio effettivamente mostrabile. Non raccogliere le preferenze personali dei minori durante il trial.

## Privacy e sicurezza
Minimizzazione, elaborazione sul dispositivo, profilazione disattivata di default, opt-in per interessi, policy firmate, revoche e scadenze, risposte generiche a utenti non autorizzati, anti-inferenza da topic sensibili. Non promettere privacy assoluta: un relay può comunque osservare metadati di trasporto; valutare il rischio insieme a UC-189.

## Anti-duplicati
UC-083 distribuisce subscription; UC-236 gestisce il filtro zona/topic; UC-239 modera pubblicazioni. **UC-248 decide sul client se e quando una notifica è pertinente e lecita, senza diffondere il profilo contestuale alla rete.**
