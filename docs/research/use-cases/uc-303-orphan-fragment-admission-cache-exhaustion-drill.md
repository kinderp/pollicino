# UC-303 — Frammenti incompleti: evitare l'esaurimento della cache dei relay

**Stato (11 novembre 2026):** proposta di sicurezza/affidabilità; solo documentazione, nessun attacco o prova eseguiti. **Difficoltà: medio-alta/alta.** Nessuna modifica a PHY LoRa, MAC, driver o firmware.

## Problema concreto

Una cache PollicinoNet riceve piccoli frammenti applicativi di molti oggetti. Un oggetto viene completato soltanto se arrivano le parti necessarie e la verifica finale `EXACT` riesce. Cosa accade se arrivano **centinaia di primi frammenti ma nessun ultimo frammento**, per semplice perdita/riavvio o per input malformato di un test? Il nodo può impegnare tutta la memoria nella ricomposizione incompleta, danneggiando altre consegne. I frammenti parziali non sono prova di un file ricevuto.

**Scenario didattico:** checkpoint fittizi denominati Messina, Villafranca e Rometta, quattro relay virtuali, cache da 16–64 KiB. Come esercizio controllato, un mittente sintetico invia molti frammenti lasciando il resto deliberatamente assente. È un test **locale e autorizzato**, non una proposta di disturbare reti o stazioni altrui.

## Attori, contratti e ruolo della rete

Mittente di prova, relay store-and-forward, collector, docente e auditor. Il ritardo opportunistico rende normale il possesso parziale di oggetti: PollicinoNet deve distinguere custodia di un oggetto verificato da spazio *temporaneamente riservato* per una ricomposizione in attesa.

- **DISCOVERY:** indizio di oggetto e spazio/capacità richiesto, senza divulgarne contenuto.
- **EXACT:** hash totale + manifest autorizzato; nessun `COMPLETE` senza verifica integrale.
- **SEMANTIC:** classe `lesson-pack`/dati IoT se ammessa; non esenta dai limiti per le quote.

Oggetto di prova: `PartialAssembly={object_id_hint, manifest_digest?, allowed_total_bytes, part_index, part_count, authorized_scope, campaign_epoch, received_verified_bytes, quota_class, expiry, status}`. Ogni frammento deve rispettare un limite di dimensioni, numero di parti e durata. Mai fidarsi di dimensioni e scadenze auto-dichiarate dal mittente senza policy locali. `QUARANTINED`, `EXPIRED`, `REJECTED`, `COMPLETE_EXACT` sono stati distinti.

## Bearer

- **LoRa:** soltanto microcapsule già consentite e supportate dall'adapter; in caso contrario la prova di frammenti avviene **solo su trasporto simulato/BLE/Wi-Fi**. Non aumentare il traffico radio per provocare congestione.
- **BLE:** frammenti locali durante incontri autorizzati e log minimi.
- **Wi-Fi/LAN/Internet:** upload di corpus di test e oggetti completi, con limiti.
- **USB/SSD/trasporto fisico:** input di test su supporti scolastici autorizzati per verificare lo stesso policy gate.

## Test software riproducibile

Tre cache virtuali (16/32/64 KiB), **1000 annunci/frammenti sintetici** per 100 possibili oggetti, soltanto 5 realmente completi. Iniettare primi frammenti ripetuti, `part_count` impossibile, manifest assente, dati fuori ordine, duplicati, un oggetto autorizzato che termina dopo un contatto molto tardivo, e casi con scadenza già trascorsa.

Confrontare due policy: `NAIVE_UNBOUNDED_HOLD` e `BOUNDED_ADMISSION` con massimo per-oggetto, per-provenienza (pseudonima e non affidabile), per-campagna e per-cache, TTL massimo ed eviction esplicita dei parziali; non discriminare volontari o identificare persone.

**Criteri di accettazione:** (1) occupazione di memoria rimane entro quota in tutte le iniezioni; (2) nessun `COMPLETE_EXACT` senza manifest/hash validi; (3) una parte duplicata non consuma una seconda quota; (4) cleanup/tombstone non fanno risorgere oggetti scaduti; (5) traffic benigno ammesso secondo regole documentate e i rifiuti/quarantene restano osservabili; (6) l'assenza di log non viene trattata come malizia del relay.

Metriche: picco RAM/disk, count di parziali, percentuale oggetti autorizzati completati, scadenze, falsi rifiuti, latenza verificata app. Non chiamare `PASS` un test non eseguito.

## Prove fisiche e perimetro sicuro

Prima in software, poi **4 schede di prova e due PC** con un workload rigorosamente limitato e programmato sull'adapter disponibile. Se non esiste frammentazione LoRa applicativa, usare Wi-Fi/USB per il volume e LoRa solo per segnali di controllo o non usarla affatto. Misurare memoria, code, crash/riavvii, stato delle parti e ricevute finali; non generare DoS, jamming o sovraccarichi sullo spettro condiviso. Una seconda campagna con checkpoint fra Rometta e Venetico è proponibile solo dopo un testbed autorizzato.

## Privacy, sicurezza e applicabilità

Tutti gli oggetti sono artificiali, nessun identificativo personale o payload reale. Autenticare manifest e autorizzazioni; limiti conservativi e cancellazione dei parziali a scadenza. Evitare di attribuire comportamenti ostili a studenti sulla base di perdita di frammenti o log mancanti. L'ammissione è una **proposta applicativa** da sviluppare e valutare, non una proprietà già implementata.

## Anti-duplicazione e riferimento

UC-262 tratta la ricomposizione corretta di microcapsule *complete*; UC-112 riprende trasferimenti grandi interrotti; UC-108 gestisce pressione delle code e backpressure; UC-240 controlla eco e cicli; UC-138 registra il mancato recapito. **UC-303 mette alla prova in modo mirato l'occupazione di risorse causata da molte ricomposizioni *mai complete* e l'isolamento delle quote**, anche quando nessun oggetto supera singolarmente le dimensioni consentite.

RFC 9171, §8, osserva che numerosi frammenti con lifetime molto lungo possono esaurire la memoria di un nodo, e che limiti di lifetime possono mitigare il rischio: https://www.rfc-editor.org/rfc/rfc9171.html . Citato come riferimento di progettazione DTN, **non** come conformità dichiarata di PollicinoNet a BPv7.
