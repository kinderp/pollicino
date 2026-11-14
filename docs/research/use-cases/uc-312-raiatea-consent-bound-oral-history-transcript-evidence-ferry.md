# UC-312 — Raiatea: memoria orale locale, trascrizioni AI e archivi distribuiti con consenso

**Stato al 14 novembre 2026:** proposta progettuale **non implementata né testata**. **Difficoltà:** alta per governance/diritti; medio-alta per prototipo sintetico. Nessuna modifica al PHY LoRa congelato, MAC, driver o firmware.

## Problema concreto
Tre scuole vogliono studiare racconti e memoria storica del territorio messinese, magari testimonianze linguistiche o tradizioni locali. Interviste e trascrizioni possono diventare utili materiali per Raiatea, ma l'audio contiene voce e dati identificabili; una trascrizione AI può sbagliare nomi o attribuire parole mai dette. Una testimonianza **è un racconto della persona**, non automaticamente una fonte verificata di ogni fatto storico. L'assenza di Internet permanente complica accesso, rettifica e autorizzazioni.

**Domanda:** come condividere *solo* materiale con diritti e consensi appropriati, associando ogni frase trascritta all'esatto segmento autorizzato e distinguendo stato automatico/revisionato?

## Attori e scenario
Archivista/docente, eventuale adulto narratore con accordo **specifico**, revisore linguistico/storico, 2-3 cache scolastiche e relay volontari. Scenario ipotetico Rometta–Venetico–Messina: un archivio scolastico raccoglie materiale autorizzato, un secondo conserva **derivati** revisionati e un terzo svolge ricerche Raiatea. Nel primo esperimento **nessuna intervista vera**, solo voci fittizie rappresentate come testo sintetico e riferimenti di segmenti virtuali.

## Perché PollicinoNet, DNA/Raiatea
PollicinoNet trasporta in ritardo annunci e richieste consentiti con store-and-forward; il controllo dell'oggetto EXACT preserva la versione di audio, trascrizione e approvazioni. Raiatea può ricercare soltanto i segmenti esplicitamente autorizzati e mostrare collegamenti ad audio/trascrizione. DNA può proporre **argomenti da verificare**, mai dedurre fatti biografici sensibili o appartenenze personali dalla testimonianza.

- **DISCOVERY:** annuncio minimale di corpus/tema pubblico e livello di accesso; non pubblicare identità, lingua minoritaria di una persona o informazioni ricostruibili.
- **EXACT:** manifest con hash delle versioni accessibili di testo/trascrizione/registrazione, `segment_start/end` (fittizi in test), consenso per finalità, ACL e revisione.
- **SEMANTIC:** temi e possibili collegamenti in Raiatea solo dopo autorizzazione; claim `NARRATED` distinto da `HISTORICALLY_CORROBORATED`.

## Bearer
- **LoRa:** manifest compatti non identificanti, disponibilità di un nuovo derivato autorizzato, stato di revoca visto dalla cache; mai audio né transcript integrale.
- **BLE:** scambio locale di brevi metadati consentiti.
- **Wi-Fi/LAN/Internet:** file audio e trascrizioni revisionate, **solo** da host/canali autorizzati.
- **USB/SSD/trasporto fisico:** archivi cifrati su supporti verificati con custodia e verifica in ingresso.

## Contratto minimo e stati
`OralRecord`: `record_id`, `source_audio_hash` opzionale, `transcript_hash`, `transcriber_kind` (human/AI), `source_segment_ref`, `reviewer_decision`, `purpose`, `consent_scope`, `access_group`, `license`, `validity_epoch`, `withdrawal_seen_at`. Stati separati:
- **RESTRICTED_SOURCE** per originale non condivisibile;
- **AI_DRAFT_UNREVIEWED** per ipotesi di trascrizione;
- **REVIEWED_FOR_ACCESS** dopo controllo umano, diritti e pubblicazione autorizzata;
- **WITHDRAWN_WHERE_OBSERVED** quando un nodo ha ricevuto revoca, senza promessa di cancellazione retroattiva su offline/copied nodes;
- **CITATION_MISSING** se la frase non ha un segmento sorgente accessibile.

Rappresentare in modo distinto la valutazione storica `NARRATED` / `INDEPENDENTLY_CORROBORATED` / `DISPUTED` / `UNKNOWN`; la revisione della trascrizione **non** equivale a corroborazione storica.

## Software immediato — non eseguito
Generare **8 racconti di prova completamente inventati**, 24 segmenti text-only, due versioni di trascrizione con errori fittizi, tre cache e autorizzazioni diverse. Consegne fuori ordine di draft, correzioni, permesso specifico di accesso e revoca. Test di ricerca con due ruoli: docente autorizzato e utente pubblico. Costruire un mini-RAG su testo sintetico che restituisce segmenti verificabili o esplicito rifiuto `CITATION_MISSING`.

**Criteri di accettazione futuri:**
1. Nessun audio, identità, trascrizione integrale o indicizzazione pubblica prima di autorizzazione documentata per quella finalità.
2. Nessun testo AI non revisionato viene pubblicato come parole autentiche di un narratore; i riferimenti ai segmenti EXACT sono verificabili.
3. Nessuna narrazione è automaticamente promossa a fatto storico comprovato; le citazioni distinguono narrazione, revisione e corroborazione.
4. Le revoche bloccano nuovi accessi dove **ricevute/verificate**; copie offline e divulgazioni passate restano un limite esplicito e richiedono procedure organizzative.
5. I relay non ricevono plaintext senza titolo; niente voiceprint/riconoscimento parlante, profili personali o dataset di voci degli studenti.

## Hardware e protocollo fisico
Per la prima prova bastano **2 PC e 4 schede LoRa**: diffusione di manifest anonimi e richieste fittizie, handoff EXACT di piccoli testi via Wi-Fi/USB, controlli ACL e review. Non serve alcuna vera registrazione audio. Per un eventuale progetto culturale reale: accordi con archivio competente, adulto consenziente, licenze e conservazione professionale, revisione umana e piano di cancellazione compatibile con le disconnessioni. Misurare ricevute applicative, accessi rifiutati e riferimenti validi, non pubblicare registrazioni automaticamente.

## Privacy, sicurezza, etica
La voce è identificabile e la trascrizione può nominare terzi, domicilio o informazioni sensibili. Le condizioni di partecipazione e pubblicazione vanno valutate con la scuola e i titolari dei diritti; quando un consenso non basta da solo, occorrono basi giuridiche e accordi adeguati. Evitare interviste a minori nella sperimentazione. Il trasporto cifrato non elimina la necessità di policy di accesso e cancellazione; nessuna revoca può recuperare copie già distribuite a terzi. Non usare questo archivio come prova certificata di eventi storici.

## Anti-duplicazione
- **UC-056/UC-076/UC-077:** consenso, policy e tombstone generali; qui particolare rapporto fra **voce, segmenti, trascrizioni e interpretazione storica**.
- **UC-060/UC-119:** media/provenienza; qui controllo etico della pubblicazione di parole pronunciate e quote segmentali.
- **UC-192/UC-288:** derivati didattici e traduzioni; qui **AI draft vs review del narratore/revisore** su fonte orale.
- **UC-296:** citazioni PDF versionate; qui segmenti e identità di un **documento sonoro** accessibile solo su autorizzazione.
- **UC-246:** confine di fiducia nell'indicizzazione; resta valido, nessuna istruzione incorporata è eseguibile.

## Linee guida esterne
- Oral History Association, *Oral History Best Practices* (consenso, revisione, preservazione e accesso): https://oralhistory.org/best-practices/
- OHA, *Core Principles* (rispetto dei narratori, limiti delle autorizzazioni e accesso): https://oralhistory.org/oha-core-principles/
