# PX20-PN-D2RP preregistration

## Identity and provenance

```text
GATE:
PX20-PN-D2RP

TITLE:
Cross-Platform Durable Persistence and Locking Validation

IDENTIFIER_STATUS:
PROVISIONAL; derived on 2026-09-13 from the explicit PX19 closure
recommendation to run a separate cross-platform durable
persistence/locking gate when Windows support is mandatory.

BASELINE:
7021e05d5c9862ca01b15aaa830db67c5f6b5b7c
```

No authoritative repository identifier for the same experiment existed after
fetching all remote refs on 2026-09-13. PX19 remains closed as
`PX19_REAL_LAN_EVIDENCE_PENDING`; this gate does not rewrite PX3--PX19
historical evidence and does not touch PILOT-014.

## Mission and hypothesis

Pollicino durable D2/D3 roots must open, lock, commit, recover and reopen on
Linux, macOS and Windows while preserving the existing bounded two-generation
snapshot format and fail-stop semantics.

```text
HYPOTHESIS:

The existing local persistence contract can be made cross-platform by
isolating OS file-locking and durability primitives below the unchanged
snapshot format. POSIX flock and Windows LockFileEx can provide equivalent
nonblocking single-writer exclusion. A platform-specific durable replacement
primitive can preserve the current rule that memory is published only after
the replacement durability boundary, without adding peer, session, transport
or application authority.
```

## Frozen behavior

- persistence envelope bytes, magic, version and two-generation selection;
- payload bounds and native validation;
- single active writer per store root;
- complete temp write and file flush before replacement;
- fail-stop and reopen after an uncertain post-replacement failure;
- no shared durable roots, peer progress state or session state;
- D2/D3/D4, B2/B2F/B2C/B2A, B4 and transport contracts.

The implementation may add only a small local filesystem backend and the
minimum call-site changes in `local_persistence.py`.

## Registered platforms

```text
WINDOWS: native Windows 11 AMD64 / CPython 3.10.7 on physical Host B
MACOS: native macOS arm64 / CPython 3.14.2 on the controller host
LINUX: native Linux CI/host execution required before READY classification
```

Compilation or mocked platform branches are not native platform evidence.
If native evidence for any registered platform is missing, the gate remains
pending/inconclusive rather than claiming three-platform readiness.

## Registered invariants

```text
PERSISTENCE_FORMAT_CHANGED = NO
PERSISTENCE_VERSION_CHANGED = NO
SINGLE_WRITER_VIOLATIONS = 0
STALE_LOCK_FALSE_POSITIVES = 0
CRASH_LOCK_RELEASE_FAILURES = 0
COMMITTED_STATE_REOPEN_MISMATCHES = 0
RECOVERY_SELECTION_MISMATCHES = 0
UNBOUNDED_PERSISTENCE_ALLOCATION = 0
MEMORY_PUBLISHED_BEFORE_DURABILITY_BOUNDARY = 0
PERSISTENT_PEER_PROGRESS_AUTHORITIES = 0
APPLICATION_SPECIFIC_PERSISTENCE_BRANCHES = 0
TRANSPORT_SPECIFIC_PERSISTENCE_BRANCHES = 0
WINDOWS_FCNTL_IMPORTS = 0
```

## Mandatory evidence

On every registered platform:

1. import and empty-root open/close;
2. D2 catalog commit/reopen and D3 query/result commit/reopen;
3. second independent process rejected while the first owns the lock;
4. hard process exit releases the OS lock and permits reopen;
5. stale lock-file contents are not interpreted as a live lock;
6. repeated alternating-generation commits and canonical reopen;
7. corrupt/truncated newest generation recovers the valid predecessor;
8. all deterministic pre/post replacement fault stages retain the registered
   old/new/fail-stop outcomes;
9. snapshot bytes produced on one OS decode unchanged on the others;
10. a focused independent-process endpoint/restart regression.

The final Linux/macOS/Windows executions must use one committed implementation
SHA and clean worktrees.

## Platform contract

POSIX retains nonblocking `flock`, file `fsync`, atomic same-directory replace
and parent-directory `fsync`. Windows will use documented Win32 primitives,
not emulated in-process locks: nonblocking exclusive `LockFileEx`, an atomic
same-volume replacement operation, and explicit file/metadata flushing where
the OS exposes it. Differences in the strongest demonstrable power-loss
guarantee must be measured and classified; they must not be hidden behind the
word “portable”.

Official references registered before implementation:

- Microsoft `LockFileEx`: <https://learn.microsoft.com/windows/win32/api/fileapi/nf-fileapi-lockfileex>
- Microsoft `ReplaceFileW`: <https://learn.microsoft.com/windows/win32/api/winbase/nf-winbase-replacefilew>
- Microsoft `FlushFileBuffers`: <https://learn.microsoft.com/windows/win32/api/fileapi/nf-fileapi-flushfilebuffers>

## Failure taxonomy

```text
A. TEST_HARNESS_ERROR
B. PLATFORM_BACKEND_IMPLEMENTATION_ERROR
C. WINDOWS_LOCKING_ERROR
D. POSIX_LOCKING_REGRESSION
E. ATOMIC_REPLACEMENT_ERROR
F. DURABILITY_BARRIER_ERROR
G. FORMAT_COMPATIBILITY_ERROR
H. CROSS_PROCESS_LOCKING_FAILURE
I. CRASH_RECOVERY_FAILURE
J. POWER_LOSS_GUARANTEE_LIMIT
K. PLATFORM_PORTABILITY_LIMIT
L. EXISTING_PERSISTENCE_CORRECTNESS_BUG
M. OUT_OF_SCOPE_FUTURE_GATE
```

A--F are repaired locally. G--I stop closure until explained and corrected.
J/K are reported quantitatively and may justify READY_WITH_LIMITS. L requires
assessment of PX5/PX6 and dependent gates before broad changes.

## Classification choices

Choose exactly one:

```text
POLLICINO_CROSS_PLATFORM_PERSISTENCE_READY
POLLICINO_CROSS_PLATFORM_PERSISTENCE_READY_WITH_LIMITS
POLLICINO_PERSISTENCE_BACKEND_EXTENSION_REQUIRED
POLLICINO_CROSS_PLATFORM_PERSISTENCE_MODEL_FALSIFIED
PX20_CROSS_PLATFORM_EVIDENCE_PENDING
PX20_PN_D2RP_INCONCLUSIVE
```

PX19 may resume only after a committed PX20 implementation has passed natively
on Windows and the same SHA is available to both physical LAN hosts. No PX20
checkpoint is created unless this gate genuinely closes.
