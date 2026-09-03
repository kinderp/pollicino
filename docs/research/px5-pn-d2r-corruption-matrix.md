# PX5 PN-D2R corruption matrix

Envelope validation occurs before state publication. Short data is truncated;
bad magic is corrupt; unknown version is unsupported; overbound declared
length is a persistence bounds violation; exact length mismatch is truncated;
digest mismatch is distinct. Only after these checks does the native PX3
decoder validate its canonical state and active bounds.

| Region | Detection |
|---|---|
| magic | `PERSISTENCE_CORRUPT` |
| version | `PERSISTENCE_VERSION_UNSUPPORTED` |
| generation | digest mismatch or invalid-generation bound |
| length | truncation or bounds violation |
| payload | digest mismatch |
| digest | digest mismatch |
| native key/reference/item/byte state | native validation translated to persistence corruption/bounds |

One valid slot plus one invalid slot always opens with explicit
`RECOVERED_PREVIOUS_GENERATION`, never an ordinary success. Zero valid slots
fail closed. Two valid, same-highest-generation, different payloads are
ambiguous and fail closed without filename preference.
