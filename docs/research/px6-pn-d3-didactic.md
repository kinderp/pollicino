# PX6-PN-D3 didactic explanation

PX3 built a bounded address book. PX5 gave every local node a durable notebook for it. PX6 adds a separate durable page for questions and candidate answers.

Suppose A writes, “I am looking for something,” then shuts down. Later B receives the bytes of that question. Pollicino does not understand them and runs no command. B's application interprets the question and replies only with keys from B's address book. The reply can survive B shutting down too. When A later receives it, A may explicitly choose a key, pull its opaque reference, and—separately—retrieve the exact content.

For FARO, the application understands RegistryQuery, packages, signatures, trust and Recommendation. For another lawful content application, its own evaluator understands its own tags. Both use the same Pollicino machinery because Pollicino sees only bounded byte IDs, opaque query bytes and catalog keys.

“Opaque” does not mean encrypted or authenticated. A result is neither truth nor a recommendation. Duplicate delivery is safe, but evaluation is not claimed to happen exactly once. No network or delivery guarantee exists in this Gate.
