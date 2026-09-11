# PX14 independent-process model

PX14 uses fresh Python interpreter subprocesses connected by binary stdin and
stdout pipes. Every worker opens exactly one caller-supplied durable root,
constructs local B2/B2F/B2C/B2A endpoint views, consumes complete protocol
messages, emits complete protocol messages, closes, and exits. No remote path,
store, or endpoint object is supplied to a worker.

The relay owns process handles and byte queues only. It may segment, coalesce,
drop, corrupt, delay, or stop forwarding bytes, but it never computes identities
or missing sets. Contact role (initiator/responder) and explicit D2 selection are
ephemeral caller policy. They are not possession evidence and are not durable.

`stdout` is protocol-only. A single JSON diagnostic line is written to `stderr`.
The experiment assumes one writer per direction and the ordered-byte property of
local pipes. It does not define a daemon, listener, multiplexing protocol, peer
identity, or transport-independent ordering guarantee.

Each protocol step uses a fresh process in the strongest restart fixtures. That
is intentionally stricter than keeping endpoint objects alive: only the durable
D2/D3 roots survive. Parent inspection of final stores occurs after workers exit
and is assertion-only.
