from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path


class LockUnavailableError(OSError):
    """The platform lock exists but another process currently owns it."""


@dataclass(frozen=True)
class LocalFilesystemCapabilities:
    backend: str
    exclusive_nonblocking_lock: str
    replacement: str
    directory_fsync: bool
    posix_modes: bool


if os.name == "nt":
    import ctypes
    from ctypes import wintypes
    import msvcrt

    _LOCKFILE_FAIL_IMMEDIATELY = 0x00000001
    _LOCKFILE_EXCLUSIVE_LOCK = 0x00000002
    _MOVEFILE_REPLACE_EXISTING = 0x00000001
    _MOVEFILE_WRITE_THROUGH = 0x00000008
    _ERROR_LOCK_VIOLATION = 33

    class _Overlapped(ctypes.Structure):
        _fields_ = (
            ("Internal", ctypes.c_size_t),
            ("InternalHigh", ctypes.c_size_t),
            ("Offset", wintypes.DWORD),
            ("OffsetHigh", wintypes.DWORD),
            ("hEvent", wintypes.HANDLE),
        )

    _kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    _kernel32.LockFileEx.argtypes = (
        wintypes.HANDLE,
        wintypes.DWORD,
        wintypes.DWORD,
        wintypes.DWORD,
        wintypes.DWORD,
        ctypes.POINTER(_Overlapped),
    )
    _kernel32.LockFileEx.restype = wintypes.BOOL
    _kernel32.UnlockFileEx.argtypes = (
        wintypes.HANDLE,
        wintypes.DWORD,
        wintypes.DWORD,
        wintypes.DWORD,
        ctypes.POINTER(_Overlapped),
    )
    _kernel32.UnlockFileEx.restype = wintypes.BOOL
    _kernel32.MoveFileExW.argtypes = (
        wintypes.LPCWSTR,
        wintypes.LPCWSTR,
        wintypes.DWORD,
    )
    _kernel32.MoveFileExW.restype = wintypes.BOOL

    CAPABILITIES = LocalFilesystemCapabilities(
        backend="windows",
        exclusive_nonblocking_lock="LockFileEx",
        replacement="MoveFileExW(REPLACE_EXISTING|WRITE_THROUGH)",
        directory_fsync=False,
        posix_modes=False,
    )

    def _windows_handle(fd: int) -> wintypes.HANDLE:
        raw = msvcrt.get_osfhandle(fd)
        if raw == -1:
            raise OSError("invalid Windows file handle")
        return wintypes.HANDLE(raw)

    def acquire_exclusive_lock(fd: int) -> None:
        overlapped = _Overlapped()
        acquired = _kernel32.LockFileEx(
            _windows_handle(fd),
            _LOCKFILE_EXCLUSIVE_LOCK | _LOCKFILE_FAIL_IMMEDIATELY,
            0,
            1,
            0,
            ctypes.byref(overlapped),
        )
        if acquired:
            return
        error = ctypes.get_last_error()
        if error == _ERROR_LOCK_VIOLATION:
            raise LockUnavailableError("Windows lock range is already owned")
        raise ctypes.WinError(error)

    def release_lock(fd: int) -> None:
        overlapped = _Overlapped()
        released = _kernel32.UnlockFileEx(
            _windows_handle(fd), 0, 1, 0, ctypes.byref(overlapped)
        )
        if not released:
            raise ctypes.WinError(ctypes.get_last_error())

    def replace_file(source: Path, target: Path) -> None:
        moved = _kernel32.MoveFileExW(
            str(source),
            str(target),
            _MOVEFILE_REPLACE_EXISTING | _MOVEFILE_WRITE_THROUGH,
        )
        if not moved:
            raise ctypes.WinError(ctypes.get_last_error())

    def sync_directory(directory: Path) -> None:
        # MoveFileExW WRITE_THROUGH is the registered Windows replacement
        # durability boundary. Windows has no direct os-level directory fsync.
        del directory

    def restrict_directory_permissions(directory: Path) -> None:
        # Windows inherits the parent directory ACL. chmod's POSIX mode model
        # would not establish an equivalent access-control guarantee.
        del directory

    def restrict_file_permissions(fd: int) -> None:
        del fd

else:
    import fcntl

    CAPABILITIES = LocalFilesystemCapabilities(
        backend="posix",
        exclusive_nonblocking_lock="flock",
        replacement="os.replace+directory-fsync",
        directory_fsync=True,
        posix_modes=True,
    )

    def acquire_exclusive_lock(fd: int) -> None:
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise LockUnavailableError("POSIX file lock is already owned") from exc

    def release_lock(fd: int) -> None:
        fcntl.flock(fd, fcntl.LOCK_UN)

    def replace_file(source: Path, target: Path) -> None:
        os.replace(source, target)

    def sync_directory(directory: Path) -> None:
        directory_fd = os.open(directory, os.O_RDONLY)
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)

    def restrict_directory_permissions(directory: Path) -> None:
        os.chmod(directory, 0o700)

    def restrict_file_permissions(fd: int) -> None:
        os.fchmod(fd, 0o600)
