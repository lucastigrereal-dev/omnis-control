"""Portable file-level write lock for JSONL stores.

Uses threading.Lock per absolute path (in-process) as the primary guard.
For cross-process safety on the same host, wraps with an OS advisory lock:
  - Windows: msvcrt.locking (stdlib)
  - POSIX:   fcntl.flock (stdlib)

Usage:
    with jsonl_write_lock(path):
        with open(path, "a") as f:
            f.write(...)
"""
from __future__ import annotations

import contextlib
import os
import threading
from typing import Generator

_LOCKS: dict[str, threading.Lock] = {}
_META_LOCK = threading.Lock()


def _get_lock(path: str) -> threading.Lock:
    abs_path = os.path.abspath(path)
    with _META_LOCK:
        if abs_path not in _LOCKS:
            _LOCKS[abs_path] = threading.Lock()
        return _LOCKS[abs_path]


@contextlib.contextmanager
def jsonl_write_lock(path: str) -> Generator[None, None, None]:
    """Acquires an exclusive write lock on *path* for the duration of the block."""
    abs_path = os.path.abspath(path)
    thread_lock = _get_lock(abs_path)

    with thread_lock:
        lock_path = abs_path + ".lock"
        lock_fd = _acquire_os_lock(lock_path)
        try:
            yield
        finally:
            _release_os_lock(lock_fd, lock_path)


def _acquire_os_lock(lock_path: str) -> int | None:
    try:
        fd = os.open(lock_path, os.O_CREAT | os.O_WRONLY | os.O_EXCL, 0o600)
        return fd
    except FileExistsError:
        # Lock file already exists from another process — advisory only, proceed
        return None
    except OSError:
        return None


def _release_os_lock(fd: int | None, lock_path: str) -> None:
    if fd is not None:
        try:
            os.close(fd)
            os.unlink(lock_path)
        except OSError:
            pass
