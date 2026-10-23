# UC-244 — Inferenza spiegabile di opportunità fra frammenti DNA/RDF offline

**Stato:** proposta documentale del 23 ottobre 2026. Nessun motore implementato o risultato sperimentale dichiarato. **Difficoltà:** alta (semantica, provenance, consenso).

## Problema concreto e storia d'uso
Tre laboratori hanno informazioni distribuite: a Venetico un gruppo pubblica una richiesta di sensori di umidità per un esperimento; a Rometta un laboratorio offre temporaneamente un kit compatibile; a Villafranca una scuola rende disponibile un banco di calibrazione. Nessuno dei tre singoli annunci è sufficiente: **solo combinando fatti compatibili nasce una possibilità di collaborazione**. I nodi possono non avere accesso contemporaneo a Internet.

Il servizio DNA non deve limitarsi a consegnare eventi GeoTopic: deve *dedurre una proposta nuova*, indicare **quali fatti e quali regole** l'hanno prodotta e consentire agli interessati di confermare o rifiutare, senza agire in automatico. Le identità e gli spostamenti degli studenti non sono parte del grafo sperimentale.

## Attori e nodi
Tre editori scolastici autorizzati; due cache/risolutori offline; un motore di inferenza locale; docente revisore; 4–8 schede PollicinoNet, alcune trasportate volontariamente e altre fisse in checkpoint autorizzati. Il contesto territoriale usa **zone pubbliche grossolane** (es. Rometta–Venetico), non coordinate delle persone.

## Perché PollicinoNet
Le parti conservano localmente piccoli *DNAFragment* versionati; PollicinoNet scopre che esistono aggiornamenti e li porta attraverso incontri intermittenti **store-and-forward**. Il motore DNA, **sopra** PollicinoNet, valida, combina e interpreta i fatti. PollicinoNet non diventa un broker RDF né assume il significato delle relazioni.

Distinguere: **fatto originario**, **ipotesi derivata**, **conferma umana** ed **esito reale**. Un'inferenza è una possibilità, non un accordo né una prova che risorse o persone siano disponibili.

## Modello minimo e contratto dei dati
Fatti sperimentali con identificatore, tipo (richiesta/offerta/risorsa disponibile), ambito, validità, autore autorizzato, livello di visibilità, revisione, identificativo completo del contenuto e riferimenti di provenienza. Possibile rappresentazione RDF con grafi nominati per sorgente/revisione; SHACL valida i vincoli strutturali. Non assumere che RDF/SHACL producano automaticamente inferenze: il motore usa **regole applicative versionate**.

Regola dimostrativa: se una richiesta valida di capacità X, un'offerta valida di X e una risorsa complementare sono pubblicamente compatibili nella stessa finestra temporale, proporre un'opportunità candidata. Ogni proposta contiene rule_id/rule_version, input_fact_ids, expiry = scadenza più restrittiva, stato PROPOSED/CONFIRMED/REJECTED/STALE, e spiegazione leggibile. Non inventare fatti mancanti né attribuire una probabilità calibrata a un semplice match logico.

## Bearer
- **LoRa:** coordinate di scoperta, ID opachi e aggiornamenti molto compatti; mai profili o grafi RDF completi in broadcast.
- **BLE:** scambio locale autorizzato di inventari e mini-manifest.
- **Wi-Fi/Internet:** recupero di frammenti/ontologie/regole e verifica documentale, con hash completo.
- **USB/trasporto fisico:** checkpoint fra scuole senza backhaul, con verifica di firma e integrità.

## Prova software immediata (senza schede)
Tre processi isolati con fixture RDF/JSON sintetiche e relay virtuali. Inserire consegne fuori ordine, frammenti duplicati, regola aggiornata, fatti revocati, TTL trascorso, schemi incompatibili e un frammento nascosto non autorizzato. Confrontare un motore di regole minimale deterministico con implementazione RDF + validazione SHACL, mantenendo identico l'output semantico consentito.

**Criteri di accettazione:** la proposta nasce solo da fatti autorizzati e validi; ogni risultato mostra la catena di provenienza; la revoca di un fatto invalida le deduzioni dipendenti quando viene appresa; l'assenza di informazioni produce stato UNKNOWN e non una falsa negazione; un relay non può visualizzare informazioni private; duplicati e riordini non moltiplicano le proposte. Conservare esempi positivi/negativi per test automatici.

## Prova fisica necessaria
4–8 schede LoRa in un primo circuito fra due laboratori, poi tre checkpoint autorizzati a Rometta/Venetico/Villafranca. Misurare TX realmente eseguiti, RX indipendenti, dimensioni dei manifest, latenza dall'ultimo fatto disponibile alla proposta validata e byte effettivamente trasferiti per bearer. Verificare anche la correttezza applicativa della deduzione: un pacchetto ricevuto non equivale a un'opportunità valida. Nessuna misura reale ancora disponibile.

## Privacy, sicurezza e limiti
Usare solo organizzazioni e inventari di prova: non inferire relazioni personali, competenze di minori, disponibilità individuali o abitudini di movimento. Consenso e controllo di accesso a livello applicativo, minimizzazione di metadati, scadenze, revoche, autenticazione degli editori, provenienza immutabile per gli oggetti validi. Il motore non deve dedurre collegamenti indiretti da attributi nascosti né rivelare in spiegazione fatti non visibili al destinatario. Revisione umana prima di pubblicare o attuare proposte.

## Distinzione dai casi già documentati
UC-011/DNATrace gestisce incontri e consenso; UC-059 ricerca opportunità di aiuto; UC-083 distribuisce sottoscrizioni; UC-115 mappa ontologie; UC-186 segnala contraddizioni; UC-236 filtra stanze GeoTopic. **UC-244 valuta invece una nuova opportunità dedotta dalla combinazione di più fatti di fonti distinte, con catena spiegabile e ritrattazione delle conclusioni.**

**Riferimenti:** W3C SHACL https://www.w3.org/TR/shacl/ ; W3C PROV-O https://www.w3.org/TR/prov-o/ . Questi sono riferimenti di progettazione, non prova di compatibilità implementata.