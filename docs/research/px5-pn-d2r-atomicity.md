# PX5 PN-D2R atomicity and filesystem scope

Commit order is: native staged clone and mutation; bounded envelope encoding;
same-directory unique temporary file; mode 0600; complete write; file `fsync`;
atomic `os.replace`; parent-directory `fsync`; then live-memory publication.
The directory is mode 0700 on the tested POSIX platform.

Failures before replace remove the temporary file where possible and leave the
old durable/live authority unchanged. Orphan `.tmp` files are never scanned as
authoritative and are harmless on restart.

After replace, an injected exception creates an uncertain acknowledgement even
if the new file parses. The live instance enters fail-stop state and every
catalog operation requires close/reopen. Reopen validates both slots and
establishes disk authority explicitly. This prevents continued operation with
memory A and disk B.

The target must be a real directory whose parent exists. Symlink targets,
symlink snapshot/lock files, plain-file targets and missing parents fail
explicitly. An unwritable directory surfaces `PERSISTENCE_IO_FAILURE`.
Temporary files are created only inside the target directory. POSIX rename and
fsync behavior is tested by deterministic `FAULT_INJECTION_MODEL`; no stronger
power-loss or cross-platform guarantee is claimed.
