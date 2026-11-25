# UC-340 — Buoni didattici monouso presso due sportelli offline

**Stato: 25 novembre 2026, proposta documentale, non implementata né testata. Difficoltà medio-alta. PHY LoRa congelato, MAC, driver e firmware invariati.**

## Problema e scenario concreto
Durante una giornata di laboratori una scuola consegna gettoni gratuiti e fittizi per ritirare un kit dimostrativo. Due sportelli scolastici possono essere offline contemporaneamente: la fotocopia dello stesso gettone potrebbe essere presentata a entrambi. Una firma autentica prova chi l'ha emesso, non che sia ancora inutilizzato. Una ricevuta tardiva non può annullare una consegna fisica già avvenuta.

Prova iniziale in due aule dello stesso istituto; replica in checkpoint autorizzati a Milazzo e Venetico, con un collector di scuola e relay degli studenti durante spostamenti ordinari e volontari. Non supporre collegamenti radio fra comuni. Attori: emittente docente, sportelli A/B, portatore di gettone fittizio, relay, verificatore e referente di audit. Nessun pagamento, biglietto reale, controllo d'accesso, documento d'identità o materiale necessario a persone vulnerabili.

## Perché PollicinoNet
Richieste, stati di riscatto e ricevute sono piccoli, possono attraversare la rete anche in differita; la rete non è un servizio di consenso sincrono. Si confrontano tre politiche:
1. controllo locale su ogni sportello (baseline deliberatamente non sicura, esclusivamente simulata);
2. assegnazione preventiva irrevocabile del singolo gettone a un solo sportello per tutta la sua validità; A può riscattarlo offline, B può solo rinviare;
3. accettazione presso qualsiasi sportello quando un unico emittente raggiungibile autorizza e registra atomicamente il consumo; se irraggiungibile, PENDING e nessuna consegna.

Non promettere simultaneamente disponibilità offline presso qualsiasi sportello e unicità del consumo durante una partizione. Non migrare l'autorità di un gettone ancora valido a un altro sportello senza riconciliazione e prova di chiusura della precedente autorità. Se lo stato persistente è incerto, bloccare il riscatto.

## Bearer e record
- LoRa: avvisi compatti e ID opachi di richieste/ricevute, entro limiti dell'adapter esistente; non trasferire credenziali segrete in chiaro.
- BLE/QR: presentazione locale di un gettone firmato; QR copiabile, non prova di consumo. Wi-Fi/LAN/Internet: sincronizzazione autorizzata del registro e contatto con l'autorità se disponibile.
- USB/trasporto fisico: riconciliazione firmata dei registri o trasporto dei kit, non confondere con consegna radio.
- DISCOVERY: stato provvisorio; EXACT: firma, hash del gettone e registro persistente del riscatto; SEMANTIC: descrizione del kit, non autorizzazione.

Voucher={campaign_id, voucher_id_random, issuer, allowed_desk, edition, expiry_policy, signature}; Redemption={voucher_id, authority_epoch, desk, operation_id, decision, receipt_hash}. Stati ISSUED, PENDING, REDEEMED, REJECTED, EXPIRED, UNKNOWN. Decisione atomica e durevole prima del rilascio; se il rilascio fisico non è attestato, gestire manualmente, non ripetere automaticamente. Il registro usato è distinto dal log di consegna.

## Software subito (piano, non eseguito)
Due sportelli, un emittente, due relay virtuali, 24 gettoni sintetici, eventi duplicati e fuori ordine. Iniettare: stessa presentazione in A/B senza contatto, replay, scadenza incerta, crash prima/dopo commit, ricevuta persa, riconciliazione tardiva e tentativo di cambio sportello.
Confrontare le politiche a parità di eventi e misurare solo nel simulatore consumi doppi, richieste PENDING, rinvii e tempo di riconciliazione. Gate: nessun doppio consumo sotto politica 2/3 se autorità unica, storage durevole e autenticazione rispettati; nessun rilascio in caso UNKNOWN; replay rende la stessa decisione senza un secondo effetto; niente promozione di PENDING in successo.

## Hardware e misure
4–6 schede LoRa, due PC di sportello e un emittente locale, QR stampati e gettoni/cartoncini. Isolare le due aule dal backhaul durante la prova, poi far trasportare le ricevute da un relay. Log indipendenti delle decisioni e dei cartoncini effettivamente consegnati. Misurare TX osservabili, ricezioni, ricevute applicative, ritardi e riconciliazione, non inventare PDR o capacità. Solo dopo autorizzazione replicare in altre sedi; nessun bisogno di tracciare persone.

## Privacy e sicurezza
ID casuali per campagna, nessuna associazione ai nominativi, firme e autenticazione degli sportelli, protezione del registro da rollback, quote e scadenze, log minimi accessibili al docente. Non usare gettoni reali, denaro, accesso a edifici, voti o servizi essenziali. Non eseguire attacchi su sistemi terzi.

## Anti-duplicazione
UC-015 riconcilia inventario; UC-026 delega a un target; UC-048 verifica credenziali; UC-175 deduplica comandi presso un esecutore; UC-194 autorizza una riserva presso il proprietario; UC-338 compone kit. Qui la domanda è l'**unicità del riscatto di uno stesso gettone copiabile a due sportelli indipendenti**, con confronto esplicito fra disponibilità offline e garanzia di non duplicazione. Estensione applicativa, non nuova primitiva radio.
