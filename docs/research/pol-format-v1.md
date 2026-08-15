# POL1 container — experimental format v1

All multibyte integers are big-endian. Fixed header fields: magic `POL1` (4 bytes), version (1), model kind (1), CDF precision bits (1), flags (1), original size (8), metadata size (4), payload bit length (8), original SHA-256 (32), model fingerprint (32). Fixed header: 92 bytes.

Model kinds: `uniform`; `static-histogram` with 256 uint16 positive frequencies; `shared-model` with no transmitted weights. A shared decoder must possess the model identified by the fingerprint and regenerate the same integer CDF at each prefix.

Validity requires exact parsed size, exact decoded byte count, SHA-256 match, and model fingerprint match before shared-model decoding. Reports must distinguish theoretical NLL/bpb, arithmetic payload bits, header/metadata bytes, external model cost, and complete `.pol` size.
