# UC-278 — Un hash pubblico può rivelare un piccolo contenuto privato?

**Stato:** proposta documentale del **3 novembre 2026**; nessun software o test fisico eseguito. **Difficoltà:** alta, soprattutto per disegno delle policy e privacy. PHY LoRa congelato, MAC e firmware invariati.

## Problema concreto e user story

Un laboratorio scambia attraverso PollicinoNet soltanto l'hash SHA-256 di un piccolo documento Raiatea o di un record DNA. Si suppone che il contenuto rimanga segreto perché nessuno vede i byte originali. Ma se il messaggio ha pochissime alternative (ad esempio `ESITO=SI` oppure `ESITO=NO` in un **dataset interamente inventato**), un osservatore può calcolare gli hash di tutte le alternative plausibili e confrontarli con quello pubblico: **non ha bisogno di invertire SHA-256**.

**Come responsabile della privacy** voglio classificare i digest e gli hint prima dell'annuncio, rifiutare la pubblicazione di riferimenti che fungano da *membership oracle* e conservare comunque la verifica EXACT riservata agli autorizzati.

## Attori, nodi e scenario locale

Editor di documenti Raiatea, motore DNA/DNATrace, tre cache scolastiche isolate, client di prova, revisore privacy, 4–6 relay volontari fra Rometta/Venetico/Villafranca. I relay inoltrano soltanto annunci **autorizzati** e non devono conoscere il contenuto o gli interessi personali degli studenti.

PollicinoNet è adatto perché `DISCOVERY` spesso usa indizi compatti mentre `EXACT` richiede l'integrità di byte e manifest. Il rischio riguarda **la visibilità degli identificativi**, indipendentemente dalla sicurezza del canale e dalla lunghezza dell'hash; gli indizi corti aggiungono ambiguità (UC-274), ma non risolvono automaticamente la privacy.

## Bearer e contratto applicativo proposto

- **LoRa:** pubblicare soltanto indizi autorizzati, opachi e non correlabili dove necessario; **mai** hash pubblico grezzo di dati a bassa entropia o informazioni sensibili.
- **BLE:** handshake autorizzato con un peer vicino, senza enumerazione pubblica della cache.
- **Wi-Fi / Internet:** manifest cifrati, credenziali, contenuti e verifiche dopo autorizzazione.
- **USB/SSD trasporto fisico:** oggetti cifrati/manifest verificati trasferiti in modo gestito fra sedi.
- `DISCOVERY`: handle casuale o tag con ambito/epoca e accesso controllato; `EXACT`: digest integrale del **contenuto corretto** verificato **dentro il perimetro autorizzato**; `SEMANTIC`: descrizione solo se divulgabile.

`AnnouncementPolicy = {content_class, audience, purpose, estimated_guessability, exposure_level, expiry, namespace_epoch, review_state}`. Un identificatore casuale non conferisce da solo autorizzazione; un tag HMAC per audience richiede gestione sicura delle chiavi, rotazione e accesso alla chiave per il verificatore. **Non confondere il sale pubblico con un segreto**: un sale pubblico non impedisce a un osservatore di indovinare fra due valori. Non pubblicare lo stesso handle stabile in più contesti se consente correlazione.

## Cosa verificare subito in software

1. Generare **solo dati fittizi**: 100 record a due/tre stati, 100 record con testo casuale e 30 capsule Raiatea sintetiche.
2. Confrontare tre politiche: A) SHA-256 del record in chiaro in annunci visibili; B) digest pubblico con sale pubblico; C) handle casuale a vita breve più manifest EXACT autorizzato (o HMAC con chiave privata quando il modello di fiducia lo giustifica).
3. Simulare un osservatore che conosce il formato dei record ma **non le chiavi**, con un dizionario di alternative ammesse; contare la capacità di identificare il contenuto, non la sola coincidenza di byte.
4. Simulare namespace/epoch differenti, annunci duplicati, key leak su una singola audience, consenso revocato, accesso senza permessi e comportamento di cache offline.
5. Verificare che i client autorizzati possano ancora ricostruire l'oggetto e controllarne EXACT, senza usare il tag di discovery come prova d'identità.
6. Report `PASS/FAIL/UNKNOWN/NOT_TESTED`, seed, politica e modello dell'osservatore; non presentare il risultato dei dati sintetici come sicurezza garantita in produzione.

**Criteri PASS:** niente pubblicazione pubblica di digest sensibili a bassa entropia; client non autorizzato non vede il manifest di prova; il client autorizzato verifica lo SHA-256 dei byte completi; una revoca non abilita nuovi annunci attraverso cache stale. I vecchi annunci osservati non sono cancellabili retroattivamente.

## Prove hardware (solo dopo il prototipo)

Due checkpoint con 4–6 schede compatibili. Trasmettere esclusivamente **annunci sintetici** nelle modalità attualmente supportate, registrare quali metadati applicativi siano osservabili sui soli endpoint controllati e verificare la propagazione e la soppressione dopo scadenza/revoca; manifest completi su Wi-Fi/USB. Non intercettare dispositivi di terzi né dati di persone. Le prove radio misurano esclusivamente la corretta propagazione degli annunci autorizzati: **non dimostrano riservatezza radio assoluta**.

## Privacy e sicurezza

Data minimization, test esclusivamente con dati artificiali, segreti fuori dai relay, ACL per manifest e HMAC, autenticazione degli editori, expiry corto, anti-replay e policy revocabili con limiti espliciti in presenza di partizioni. Distinguere guessing di un contenuto, linkability fra annunci e accesso ai byte: sono rischi differenti. Non affermare che la cifratura del payload protegga automaticamente il significato dei digest pubblici.

## Differenza dai casi esistenti

**UC-274** tratta collisioni tra hint diversi e verifica dell'identità EXACT; **UC-189** studia la correlabilità dei metadati passivi; **UC-021/152** trattano segretezza dei contenuti e inventari. **Qui l'esperimento mostra che un digest perfettamente corretto e senza collisioni può rivelare il valore originale attraverso un dizionario piccolo**, proponendo una *policy gate* per gli annunci e distinguendo integrità da confidenzialità.

## Fonte di riferimento

- RFC 6920, §10 *Security Considerations*: https://www.rfc-editor.org/rfc/rfc6920.html#section-10 — un nome basato su hash può consentire di indovinare contenuti poco variabili e non ne garantisce la riservatezza.
