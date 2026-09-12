# PX17-PN-B6 B4 frame reader

## Executable envelope audit

The closed B4 header is `struct.Struct(">4sBB32sIHHHI")`, exactly 52 bytes:

| Field | Bytes | Reader use |
| --- | ---: | --- |
| magic | 4 | fail current stream if wrong |
| version | 1 | reject unknown version |
| type | 1 | reject unknown type |
| message SHA-256 | 32 | B4 reassembly authority, not stream delimiter |
| total B2-message length | 4 | bounded B4 metadata validation |
| fragment index | 2 | bounded B4 metadata validation |
| fragment count | 2 | bounded B4 metadata validation |
| payload length | 2 | frame delimiter |
| payload CRC32 | 4 | complete-frame structural integrity |

`52 + payload_length` uniquely determines the next frame length on an ordered
byte stream.  No extra prefix, delimiter, escape scheme, or outer magic was
required.

## Incremental behavior

The inherited reader accepts arbitrary chunks.  It buffers only toward the
fixed header or declared bounded frame length.  One-byte headers and payloads,
header/body splits, fixed-seed segmentation, concatenated frames, and multiple
complete frames plus a partial suffix all produced segmentation-independent
frames.

Clean EOF at a frame boundary is a normal transport end.  EOF with any buffered
header or payload raises a deterministic incomplete-frame error.  Complete
earlier frames stay valid; the incomplete final frame never reaches B4
reassembly.

## Fail-stop corruption rule

Wrong magic, invalid type/version, impossible bounds, CRC failure, and a
deleted-byte desynchronization terminate the current stream opportunity.
There is no scan for a later magic sequence:

```text
UNBOUNDED_STREAM_RESYNC_SCAN = 0
```

This is deliberately conservative.  A fresh connection/contact reconstructs
all needed work from durable receiver state.

## Allocation discipline

The payload length is checked against the configured B4 frame ceiling before
the body is read.  The maximum configured frame is 4096 bytes; the default
read size is the same ceiling.  Pending complete frames from one read plus an
incomplete suffix are bounded by the frame/read configuration.  No received
length controls an unbounded allocation.

## Layering

The reader validates only enough B4 structure to delimit a bounded frame and
then invokes the existing B4 frame codec.  B4 reassembly still validates
message shape and SHA-256; B2 still validates its complete message; native
D2/D3 still owns atomic durable apply.
