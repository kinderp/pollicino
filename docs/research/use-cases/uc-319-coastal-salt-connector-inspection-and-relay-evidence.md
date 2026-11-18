# UC-319 — Checkpoint costieri: deposito salino, connettori e diagnosi dei guasti

**Stato:** proposta di ricerca del 18 novembre 2026; nessun test software o fisico eseguito. **Difficoltà:** medio-alta (alta per conclusioni causali sulla durata). Non toccare il PHY LoRa congelato, MAC, firmware o driver.

## Problema risolto e storia concreta
Un checkpoint scolastico fisso vicino alla costa tirrenica messinese può apparire «fuori rete». Il docente potrebbe attribuirlo alla copertura LoRa, mentre la causa potrebbe essere un connettore degradato, una guarnizione danneggiata, una cattiva alimentazione o un guasto completamente diverso. Serve distinguere **osservazione visiva, difetto elettrico verificato, manutenzione e recupero delle consegne**. Non si deduce corrosione dalla sola vicinanza al mare e non si deduce una causa da un RSSI basso.

**Storia:** «Come responsabile del checkpoint voglio conservare la storia delle ispezioni e verificare se una manutenzione documentata coincida con un cambiamento misurabile di disponibilità, senza dichiarare una causa non dimostrata».

## Attori e contesto messinese
Due postazioni di confronto autorizzate (ad esempio una sede costiera nei pressi di Rometta Marea e un banco indoor), docente/manutentore, quattro schede o più, collector indipendente e relay studenteschi volontari. In un secondo tempo: checkpoint autorizzati nell'area Spadafora–Venetico–Milazzo. Non assumere copertura radio tra queste località. PollicinoNet conserva diagnostiche piccole quando manca Internet e trasporta in differita il fascicolo completo di ispezione.

## Bearer e modello dati
- **LoRa:** annunci di stato, contatore di avvii, hash di rapporti e richieste di manutenzione *solo se supportati* dall'adattatore e dai limiti radio esistenti.
- **BLE:** diagnostica di prossimità se la scheda e il software la supportano.
- **Wi-Fi/Internet:** trasferimento dei registri e delle foto, accesso supervisionato al cruscotto.
- **USB/SD/trasporto fisico:** estrazione dei log o trasferimento di un componente guasto verso il laboratorio.

Schema proposto, non implementato: `Inspection={campaign_id,coarse_site_id,board_hw_revision,enclosure_profile,inspection_id,observed_at_with_uncertainty,connector_visual_state,optional_contact_test,boot_count,uptime_evidence,service_action,photo_hash,log_hash,review_status}`. Gli stati `OBSERVED`, `TESTED`, `UNKNOWN` e `REVIEWED` non sono sinonimi.

## Cosa provare in software, ora
Creare 2 siti fittizi, 30 osservazioni per sito, log incompleti, reset, foto mancanti e interventi programmati; associare ogni misura al relativo `inspection_id`. Verificare che:
1. un miglioramento dopo una pulizia non venga dichiarato automaticamente prova di corrosione;
2. dati mancanti e sensori in disaccordo producano `UNKNOWN`;
3. un difetto fisico non venga registrato come «perdita LoRa» in assenza di log RX/TX;
4. duplicati, revoche e osservazioni tardive non cancellino l'evidenza precedente.
Metriche software: completezza dei dossier, falsi stati di «riparato», riconciliazioni corrette, rapporti non verificabili. I numeri del dataset sono **input di test**, non dati osservati.

## Quale hardware e quali prove reali
Iniziare in laboratorio con 4 schede, 2 alimentazioni controllate, 2 PC/logger, connettori ispezionabili e fotografie standardizzate. Per prove su postazioni fisse: rilevare alimentazione, boot e applicazione; utilizzare controlli periodici non invasivi e prove appaiate prima/dopo manutenzione, con ricevute applicative e ricevitori indipendenti. **Non spruzzare acqua salata su elettronica o batterie alimentate** e non improvvisare camere di nebbia salina. Servono procedure di sicurezza, autorizzazioni e osservazioni ripetute per ogni ipotesi di degrado.

## Privacy, sicurezza, limiti e anti-duplicati
Soltanto codici dei siti approvati; no indirizzi di casa, spostamenti, foto di persone o nomi degli studenti nei report. Ruoli autorizzati per manutenzione, foto controllate, log firmati dove possibile, retention definita. La diagnostica non deve divulgare chi ha trasportato la scheda.

**Differenze:** UC-214 controlla l'**umidità dentro l'involucro**, UC-113 inoltra **ticket di manutenzione**, UC-206 valuta la **prontezza prima delle prove** e UC-283 l'**installazione nell'edificio**. Qui la domanda distinta è la **qualità dei connettori e delle ispezioni in ambiente costiero**, legata a un'ipotesi di guasto da verificare fisicamente. Il manuale Schneider Electric descrive depositi salini e possibili malfunzionamenti elettronici in ambienti salini, ma non fornisce alcuna misura dei nostri checkpoint: https://productinfo.se.com/ntnwmaintenanceguide/lvped508016-nt-nw-maintenance-guide/English/BM_MasterPact%20NT_NW%20Maintenance%20Guide_0000517969.xml/%24/TPC_MTZmaint_Influence_Salt_Environment_Aging_354b1ab7_T000215613 .

**Gate:** nessuna affermazione su corrosione, copertura o durata senza evidenze indipendenti e un disegno di confronto; nessuna modifica al PHY congelato.
