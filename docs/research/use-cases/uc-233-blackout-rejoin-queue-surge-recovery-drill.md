# UC-233 — Recupero ordinato delle code dopo il rientro simultaneo dei relay

**Stato:** proposta documentale del 20 ottobre 2026; solo esercitazione controllata.

## Problema
Quando una classe di schede torna connessa dopo molte ore di isolamento, tutte possono pubblicare inventari e ritrasmettere messaggi nello stesso momento. Le code si saturano, i contenuti possono essere duplicati e le autorizzazioni locali risultare obsolete. Come riportare il servizio in funzione gradualmente senza presumere che tutti gli orologi siano corretti?

## Attori e scenario
6–12 relay virtuali, due cache di laboratorio e un collector. Nella simulazione sono presenti gruppi di checkpoint scolastici fra Messina, Villafranca e Venetico. Nessuna infrastruttura elettrica pubblica viene coinvolta: gli scenari territoriali sono **fittizi**.

## Perché PollicinoNet; bearer
LoRa per digest e controllo piccolo; BLE/Wi-Fi/LAN per blocchi verificati; Internet facoltativo; USB/SD per recuperi manuali. Store-and-forward conserva code durante la disconnessione, poi permette riconciliazione e ricevute successive. Il PHY LoRa rimane invariato.

## Test software immediato
Confrontare tre politiche sui medesimi 12 nodi sintetici: (a) avvio di tutte le sessioni subito; (b) avvio distribuito e limiti per coda; (c) riconciliazione dei digest prima dei trasferimenti. Iniettare clock incerti, spegnimenti, ritardi, doppie consegne e priorità diverse. Misurare **solo in simulazione** numero di richieste, picco delle code, byte verificati, tempo di convergenza e messaggi mai recuperati. Validare che un messaggio già accettato non produca due effetti applicativi.

## Prova fisica necessaria
4–8 schede, due PC, rete isolata e alimentatori a bassa tensione in laboratorio. Interrompere e riattivare solo i dispositivi sperimentali; raccogliere realmente tempi di collegamento, trasferimenti e ricevute. Non simulare guasti ai servizi scolastici e non dichiarare PDR/throughput fisici prima dei test.

## Privacy/sicurezza e difficoltà
Capsule, identità e autorizzazioni di test; limiti di ritrasmissione, verifica delle epoch di autorizzazione, nessuna attuazione reale. Difficoltà **alta**. Obiettivo: recupero progressivo e auditabile, con stato esplicito per i contenuti non ancora recuperati.

## Originalità
UC-108 è backpressure, UC-143 è disponibilità del nodo, UC-175 è idempotenza e UC-201 è dismissione. **UC-233 testa l'effetto collettivo del rientro contemporaneo** come problema di resilienza di sistema.
