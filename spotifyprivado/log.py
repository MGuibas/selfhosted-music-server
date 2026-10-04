import threading

_lock = threading.Lock()


def log(msg: str) -> None:
    with _lock:
        try:
            print(msg, flush=True)
        except UnicodeEncodeError:
            print(msg.encode("ascii", errors="replace").decode("ascii"), flush=True)
