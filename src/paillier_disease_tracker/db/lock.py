from __future__ import annotations

from contextlib import contextmanager
import os
from pathlib import Path
import sys
import time

if sys.platform == "win32":
    import msvcrt
else:
    import fcntl


@contextmanager
def acquire_db_lock(db_path: Path | str, timeout: float = 120.0, poll: float = 0.1):
    lock_path = Path(db_path).with_suffix(Path(db_path).suffix + ".lock")
    lock_path.parent.mkdir(parents=True, exist_ok=True)

    handle = open(lock_path, "a+")
    handle.seek(0, os.SEEK_END)
    if handle.tell() == 0:
        handle.write("0")
        handle.flush()

    start = time.monotonic()
    acquired = False

    try:
        while True:
            try:
                if sys.platform == "win32":
                    msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
                else:
                    fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                acquired = True
                break
            except OSError:
                if time.monotonic() - start >= timeout:
                    raise RuntimeError(
                        "Database is busy. Another instance is running an operation."
                    )
                time.sleep(poll)

        yield
    finally:
        if acquired:
            try:
                if sys.platform == "win32":
                    msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
                else:
                    fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
            finally:
                handle.close()
        else:
            handle.close()
