# PX8-PN-D4 didactic explanation

PX6 gave every node a durable mailbox and PX7 let FARO use it. PX8 models two
people meeting briefly. They compare what each already has, exchange only what
fits before they separate, and keep everything successfully received in their
own notebook. Hours later they can meet again—or meet somebody else—and
continue from the notebooks instead of starting over. Nothing in this logic
knows whether a future meeting happens over LoRa, Bluetooth, Wi-Fi, or a cable.

The notebook is the important part. There is no second notebook saying “during
session 17 I sent messages 1 through 4.” If four records were committed, the
receiver already proves it has those four. A later encounter compares current
notebooks and starts with the fifth missing record. Deleting the old contact
report changes nothing.

A query is a sealed application note, not a command. Mule C can carry it without
reading or executing it. B may later evaluate it outside the contact, write a
result, and let C carry that result back. A result is still only a candidate
statement. References, package bytes, verification, trust, and import remain
explicit later choices.

This is store-carry-forward state behavior, not routing or custody. The harness
chooses meetings, senders keep their copies, and no eventual delivery promise is
made.
