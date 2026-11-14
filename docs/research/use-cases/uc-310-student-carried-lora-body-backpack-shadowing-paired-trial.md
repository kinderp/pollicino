# UC-310 — LoRa trasportata dagli studenti: corpo, zaino e orientamento in un esperimento appaiato

**Stato al 14 novembre 2026:** proposta didattica; **nessuna prova eseguita**. **Difficoltà:** medio-alta. Nessuna modifica a PHY LoRa congelato, MAC, driver, firmware o impostazioni di trasmissione.

## Problema e domanda
Una scheda che comunica appoggiata su un tavolo può comportarsi diversamente quando è trasportata in tasca o in uno zaino, oppure quando il corpo si trova tra antenna e checkpoint. Non possiamo attribuire una mancata consegna al solo corpo umano senza controllare posizione, orientamento, altezza, alimentazione, ambiente e log.

**Domanda verificabile:** con uno stesso checkpoint autorizzato, quanto cambiano ricezioni osservate e **consegne applicative EXACT** fra dispositivo su supporto fisso, accanto a uno zaino vuoto e dentro uno zaino portato da un volontario fermo, con orientamenti controllati? Evitare di imporre prove su persone: un manichino/supporto inerte è utile come controllo, ma non sostituisce una misura su persona.

## Attori, nodi, scenario
Docente sperimentatore, due ricevitori indipendenti se disponibili, un relay LoRa scolastico, quattro-sei schede totali, PC che producono log e **un solo volontario adulto o partecipante idoneo con consenso esplicito**. Esempio: cortile scolastico autorizzato a Rometta; replica successiva a Venetico, non collegamento radio presunto fra i due comuni. Nessuna attività durante spostamenti degli studenti e nessuna osservazione delle loro presenze.

## Perché PollicinoNet
Il relay store-and-forward potrebbe incontrare checkpoint in condizioni di trasporto differenti. Serve separare **un contatto radio plausibile** dalla ricezione di un messaggio e dalla sua successiva accettazione applicativa; quando il contatto non è utile, il contenuto resta custodito per un nuovo incontro. Questa prova informa le regole operative dei relay, non cambia la radio.

- **DISCOVERY:** annunci opachi di un run di laboratorio autorizzato; niente identificatori personali.
- **EXACT:** ID di capsule sintetiche, ricevute applicative, registro trasmissioni e denominatori osservabili.
- **SEMANTIC:** solo descrizioni delle condizioni sperimentali; nessuna inferenza su identità, corpo o percorsi.

## Bearer
- **LoRa:** capsule minime già supportate dall'adapter, stesso PHY congelato e stessi parametri legalmente ammessi, traffico limitato.
- **BLE:** esportazione locale di log e checkpoint di stato, se supportata.
- **Wi-Fi/Internet/LAN:** raccolta dei log e report **dopo** il test; non assumerne la disponibilità sul campo.
- **USB/trasporto fisico:** esportazione di log e dataset sintetici su supporti scolastici autorizzati.

## Software immediato — ancora non eseguito
Simulare **5 condizioni × 3 rotazioni × 20 tentativi nominali** con seed fisso, ingressi di ricezione sintetici e log mancanti. Le cinque condizioni sono: supporto fisso; zaino vuoto accanto al supporto; zaino portato fermo rivolto verso RX; zaino portato fermo rivolto altrove; supporto fisso ripetuto come controllo finale. Un modulo costruisce il denominatore dalle TX attestate, non dai messaggi attesi; un altro produce ricevute EXACT fittizie e stati **RECEIVED**, **ACCEPTED**, **NOT_OBSERVED**, **UNKNOWN_LOG**. Il simulatore non rappresenta una curva fisica RF.

**Criteri di accettazione per un futuro test:**
1. Nessun successo viene dichiarato senza ricevuta dell'app destinataria, nessuna perdita RF certa se i log RX/TX sono incompleti.
2. I confronti sono appaiati, con ordine delle condizioni alternato, due controlli fissi e descrizione della geometria; dati non comparabili sono marcati.
3. Riferire TX confermate, RX osservate e accettazioni come quantità **distinte**, evitando percentuali su denominatori ignoti.
4. La partecipazione personale è facoltativa, revocabile e non compare nei log; niente localizzazione, foto identificabili o percorsi.
5. Non usare valori presunti di RSSI, portata, PDR o energia come risultato PollicinoNet.

## Prove hardware necessarie
Prima banco/cortile autorizzato con 4-6 schede, alimentazione verificata, posizioni segnate su schema **non personale**, due PC e preferibilmente due osservatori RX; sessioni statiche, **senza muoversi in strada**. Raccogliere configurazione dichiarata e verificata, numero TX effettive, RX indipendenti quando disponibili, ricevute app, eventuale RSSI/SNR **solo se esposti da interfacce già disponibili**. Non alterare il PHY o aggiungere log invasivi ai driver. Una fase provinciale può ripetere il protocollo in scuole differenti **senza dedurre copertura tra comuni**.

## Sicurezza, privacy e confini
Verificare permessi scolastici, regole radio vigenti, alimentazione, fissaggio dell'antenna e compatibilità RF; niente antenne a contatto con persone se non è stata valutata la sicurezza. Niente sperimentazioni invasive, niente dati personali o monitoraggio di studenti. I risultati dipendono dall'hardware concreto e dall'ambiente: nessuna generalizzazione senza repliche.

## Anti-duplicazione
- **UC-211:** montaggio dell'antenna su un'installazione; **qui** confronto appaiato del relay **trasportato**, con schermatura e orientamento del corpo/zaino.
- **UC-280:** abitacolo di veicolo parcheggiato; **qui** custodia personale statica senza veicoli.
- **UC-232/UC-277:** asimmetria e punti di perdita radio/app; qui la variabile d'interesse è **la modalità di trasporto fisico**.
- **UC-304:** contatti affollati e brevi; qui un solo invio controllato alla volta.

## Riferimenti esterni (non risultati di PollicinoNet)
- Van Torre et al., *Wearable 868 MHz LoRa wireless sensor node*, documenta la dipendenza di collegamenti wearable da condizioni corporee e orientamento: https://biblio.ugent.be/publication/8632901
- *Effects of Body Shadowing in LoRa Localization Systems*, ricerca su ombreggiamento corporeo; frequenze/hardware/metodi non sono automaticamente trasferibili: https://doaj.org/article/72b2eed878ea436784b9fc0b657eb5de
