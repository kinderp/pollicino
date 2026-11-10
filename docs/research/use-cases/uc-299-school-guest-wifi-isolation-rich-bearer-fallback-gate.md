# UC-299 — Wi-Fi ospiti isolato: passaggio a un bearer realmente funzionante

**Stato:** proposta documentale del 10 novembre 2026. Non implementata, nessuna misura. **Difficoltà:** medio-alta (configurazioni di rete, negoziazione, permessi e sicurezza). Nessun cambiamento a PHY LoRa congelato, MAC, driver o firmware.

## Problema concreto

Due PC scolastici si collegano allo **stesso SSID ospiti**, ma non possono trasferirsi un documento Raiatea: l'access point può isolare i client, imporre un captive portal o consentire Internet senza scambio P2P. L'icona «Wi-Fi connesso» non dimostra un contatto applicativo utilizzabile. Se PollicinoNet annuncia un PDF via LoRa e poi prova un handoff Wi-Fi non consentito, la richiesta non deve cadere nel vuoto né aggirare le regole della scuola.

**Storia:** «Come docente voglio distinguere Wi-Fi associato, peer raggiungibile, autorizzazione all'app e ricezione dell'oggetto esatto; se lo scambio LAN non è ammesso, voglio un fallback legittimo senza presumere che Internet risolva».

## Attori, nodi e valore PollicinoNet

Due PC o gateway della scuola, AP di **laboratorio** gestito dall'amministratore, un checkpoint, due cache, 4 schede LoRa opzionali, eventuale telefono scolastico, relay store-and-forward degli studenti. Scenario: laboratorio di Rometta che annuncia il manifest di un pacchetto didattico; destinatario a Venetico lo acquisisce in altro incontro BLE/USB o tramite una rete separata espressamente autorizzata.

PollicinoNet è adatto perché l'oggetto può rimanere in coda finché compare un bearer realmente praticabile: **scoperta e identificazione non equivalgono a trasferimento riuscito**. Non bypassare l'isolamento dell'SSID o il captive portal con tunnel non approvati.

## Bearer e stati del contratto

- **LoRa:** annuncio compatto di oggetto/manifest, richiesta e stato nelle capacità dell'adapter esistente; non veicolare il PDF.
- **BLE:** controllo locale e piccoli metadati soltanto su dispositivi che lo supportano, previo consenso.
- **Wi-Fi/LAN:** trasferimento di contenuti solo con peer reachability, TLS/autenticazione, ACL e policy consentite. **Internet:** via gateway approvato solo dove ammesso, non come assunzione implicita.
- **USB/SSD/trasporto fisico:** fallback gestito per file più grandi con hash EXACT, autorizzazione e import sicuro (UC-294).

`HandoffProbe={run_id,profile_id,ssid_class: LAB_OPEN|LAB_ISOLATED|LAB_PORTAL,association_state,peer_discovery_state,peer_connect_state,authorization_state,object_hash,transfer_state: NOT_ATTEMPTED|BLOCKED|PARTIAL|EXACT_VERIFIED|UNKNOWN,app_receipt_id?,evidence_quality}`. L'associazione Wi-Fi e un DNS riuscito **non** portano a `EXACT_VERIFIED`. Qualsiasi trasferimento parziale rimane riprendibile; non dedurre cause di fallimento senza log. Rispetta il rifiuto di permessi «Local Network» su iOS, quando applicabile.

## Esperimento software subito

Tre profili di rete simulati: (A) LAN P2P consentita, (B) associazione + Internet ma client isolation, (C) captive portal/non autorizzato. Iniettare discovery mDNS disponibile ma socket bloccato, socket attivo ma autenticazione fallita, permesso locale negato, assenza Internet, handoff BLE interrotto, oggetto parziale e duplicati dopo il ripristino. Confrontare politica ingenua «SSID uguale = peer pronto» con `PROBE+POLICY+EXACT`.

**Criteri PASS:** nessun file marcato consegnato senza hash completo e ricevuta dell'app; zero tentativi verso bearer vietati dalla policy; fallback BLE/USB o attesa esplicita; nessuna consegna doppia applicativa dopo resume; cause UNKNOWN quando non distinguibili. Metriche: completamenti **simulati** entro deadline, byte, tempo al receipt e violazioni di policy (attese zero).

## Verifica hardware

Solo con autorizzazione dell'amministratore usare **un access point proprio di laboratorio** e due PC, configurando in sequenza SSID normale, isolamento client e captive portal sintetico. Non modificare reti scolastiche di produzione e non fare scansioni non autorizzate. Osservare il traffico **solo dei dispositivi di test**, la connessione applicativa, l'integrità EXACT e l'eventuale ripresa via BLE/USB. Le quattro schede LoRa servono *soltanto* dopo la verifica della compatibilità adapter e delle regole radio. Ripetere poi in un'altra sede autorizzata (es. Venetico); nessuna affermazione sulla Wi-Fi delle scuole reali finché non è misurata.

## Privacy, sicurezza e differenze

Niente SSID identificativi di famiglie, log di indirizzi MAC permanenti o traffico di terzi; certificati verificati, accesso minimo, cifratura, autorizzazione dei manifest, retention ridotta. La prova non deve disattivare ACL o captive portal di altri utenti. UC-092 verifica **connettività Internet generale**, UC-033 l'handoff sicuro, UC-124 la scelta del bearer, UC-297 lo stato del telefono. **UC-299 testa l'effettiva raggiungibilità P2P LAN sotto isolamento e permessi, e il fallback conforme alle regole.**

## Fonti tecniche di riferimento

- Cisco Meraki, wireless client isolation: https://documentation.meraki.com/Wireless/Operate_and_Maintain/How_Tos/Firewall_and_Traffic_Shaping/Wireless_Client_Isolation
- Apple, local-network permission: https://support.apple.com/en-me/102229
- [UC-294](uc-294-offline-removable-media-untrusted-intake-gate.md), [UC-275](uc-275-lora-marginal-value-no-lora-control-trial.md).
