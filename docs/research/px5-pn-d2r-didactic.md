# PX5 PN-D2R didactic report

PX3 built the address book. PX4 proved FARO can use it. PX5 now gives each node
a notebook where that address book survives shutdown.

The notebook still contains only byte keys and opaque reference bytes. It does
not suddenly learn what FARO science, publisher trust, applicability or
Recommendation mean. Its checksum says whether the notebook was damaged; it
does not say whether any entry is true or trustworthy.

Each node keeps two pages: the newest committed page and the immediately
previous one. If the newest is damaged, the node says explicitly that it
recovered the older page. If both are damaged—or two pages make incompatible
claims about the same generation—the node refuses to guess.

A write is prepared using the existing PX3 rules, flushed to a temporary file,
atomically renamed, and only then shown as live. If failure happens after the
rename, the object stops until reopening can decide what disk actually holds.
This is local restart safety, not networking, consensus or a database service.
