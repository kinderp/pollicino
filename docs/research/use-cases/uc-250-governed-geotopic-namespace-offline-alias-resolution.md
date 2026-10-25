# UC-250 — Namespace GeoTopic governato e risoluzione degli alias offline

**Stato:** proposta documentale del 25 ottobre 2026; non implementata, nessun test eseguito. **Difficoltà:** medio-alta.

## Problema concreto
Due laboratori creano contenuti per Rometta mentre uno è offline. Uno usa il nome canonico del luogo, l'altro un alias; un terzo prova a registrare lo stesso topic di primo livello. Senza regole, un messaggio potrebbe apparire nella stanza sbagliata o un alias potrebbe dirottare lettori verso un editore non autorizzato. I relay non devono decidere autonomamente quali luoghi esistano.

**User story:** «Come docente di un laboratorio di Venetico, voglio creare un sottotopic per un esperimento sotto un luogo già approvato, pubblicare offline e farlo arrivare correttamente dopo giorni senza dover modificare il nome del luogo».

## Attori e nodi
Registro/autorizzatore della piattaforma, amministratore scolastico, editori di topic, creatori di sottotopic, cache di scuole, relay volontari degli studenti, client lettori, verificatore di firme. Testbed: checkpoint autorizzati a Messina, Villafranca, Rometta e Venetico; **nessuna localizzazione dei portatori**.

## Regole del namespace applicativo
Forma canonica: `percorso.geografico#topic.sottotopic`. Il solo `#` indica il topic predefinito del luogo. I percorsi geografici e i topic **di primo livello** sono assegnati o approvati dalla piattaforma; dal **secondo livello** gli utenti autorizzati possono creare sottotopic, secondo la policy del ramo. Ogni luogo deve prevedere anche un ramo di primo livello riservato ai sottotopic liberamente creati, ma **il nome di quel ramo è ancora da decidere**: rappresentarlo come `<RAMO_UTENTI_DA_NOMINARE>`, senza fissare un nome prematuramente.

Un luogo ha un identificatore canonico unico, eventualmente con alias firmati e versionati. La registrazione di un nuovo luogo può richiedere approvazione e topic iniziali. Non si creano luoghi o room tracciando poligoni arbitrari. BLE, GPS, LoRa e Internet aiutano a scoprire o trasportare gli oggetti ma **non modificano il namespace**.

Esempio solo dimostrativo, soggetto ad approvazione: `italia.sicilia.messina.rometta#ambiente.orto`; un eventuale alias più leggibile risolve allo stesso ID, mai a un nuovo luogo.

## Perché PollicinoNet e bearer
LoRa può portare annunci minimi con `place_id`, digest del manifest, versione, scadenza e ID opaco di topic. BLE trasporta manifest/alias brevi tra nodi vicini. Wi-Fi e Internet scambiano il registro firmato e i contenuti GeoTopic; USB o trasporto fisico consegnano snapshot del registro in reti separate. Store-and-forward separa **distribuzione** da **autorità**: una copia inoltrata non può assegnare un nome.

## Contratto e invarianti
Registro firmato `PlaceManifest(place_id, canonical_path, approved_topic_roots, policy_version, revision, valid_until, issuer)`. Mapping firmato `Alias(alias, canonical_place_id, revision, valid_until)`. Un `SubtopicCreation` prova l'autorizzazione e la policy del ramo con `parent_topic_id, creator_pseudonym, nonce, revision`.

- Un nome canonico non può designare due `place_id` differenti; collisioni => `CONFLICT/QUARANTINED`, mai risoluzione arbitraria tramite «ultimo messaggio arrivato».
- L'alias non conferisce privilegi e non sostituisce identità o firme del contenuto.
- Nuovi luoghi e nuovi topic radice non vengono autorizzati da relay scollegati.
- In assenza del manifest valido, un client non deve presentare la stanza come approvata; gli eventi possono attendere verifica senza essere cancellati silenziosamente.
- Revoche, scadenze e versioni non devono essere riattivate da repliche vecchie.

## Prova software subito
Due registri offline e otto relay virtuali; creare tre luoghi approvati e topic simulati, alias omonimi, richieste non autorizzate di topic radice, sottotopic uguali in luoghi differenti, messaggi fuori ordine, clock skew e aggiornamenti persi. Verificare: zero collisioni accettate; nessun alias non firmato sposta un messaggio; `#` risolve solo al default corretto; il bearer non cambia l'ID; nessun utente promuove una sottostanza a topic radice.

Misure: numero di risoluzioni corrette/respinte, byte del manifest e delle notifiche, tempo di convergenza dopo la riunione delle partizioni, conflitti lasciati espliciti. Usare fixture senza persone reali.

## Hardware reale
Prima prova con 4–8 schede compatibili, due PC come cache/registro e due checkpoint scolastici. Inviare hash e notifiche LoRa, poi recuperare manifest e post tramite BLE/Wi-Fi; ripetere con USB. Misurare TX/RX indipendenti, byte, durata dei contatti e stato applicativo: **un annuncio LoRa ricevuto non dimostra che la stanza sia stata autorizzata**.

## Privacy e sicurezza
Non usare coordinate di casa, percorso dei minori, identità reali o topic sensibili nel broadcast. Firmare il registro, controllare i permessi dei creatori, limitare retention e accesso, considerare gli alias metadati potenzialmente correlabili. Opt-in, sospensione locale e revisione scolastica per trial territoriali. Nessun diritto applicativo deriva dalla semplice prossimità BLE.

## Perché non duplica casi esistenti
UC-067 risolve nomi di servizi; UC-083 gestisce sottoscrizioni; UC-236 distribuisce eventi stanza+zona; UC-247 gestisce il ciclo di vita di room effimere; UC-239 la moderazione. **UC-250 governa invece l'assegnazione dei nomi territoriali, delle radici e degli alias, in presenza di repliche disconnesse e privilegi differenti.** Non introduce modifiche al PHY LoRa.
