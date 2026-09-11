# PX12-PN-B2C complexity analysis

The experimental IBLT uses three hash indexes and `2 * capacity + 31` cells.
Each cell is 14 encoded bytes. Capacity is bounded to 1,000, giving 2,031 cells,
28,434 bytes of decoder cell storage, and a 28,517-byte summary. Every message
remains below the inherited 29,245-byte B2 complete-unit limit.

Build work is linear in local identities times three hashes. Decode work is
linear in receiver identities times three plus peel operations. No state is
persisted. Repeating a large sketch on every finite contact is costly: the
1,000-difference/10,000-state run used 413,452 control bytes over 11 contacts,
versus 190,785 for PX11 exact B2F.

No third-party dependency was added. A Minisketch/BCH implementation was not
justified by this gate's evidence. The IBLT implementation is isolated in one
new production module and has explicit encoding, memory, capacity, attempt, and
message bounds.
