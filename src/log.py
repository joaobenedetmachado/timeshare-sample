"""Short terminal lines. Success is green. A miss is one plain sentence."""

import os
import sys

_GREEN = "\033[32m"
_RESET = "\033[0m"
_READY = False


def success(message: str) -> None:
    _prepare()
    line = f"ok  {message}"
    if _use_color():
        line = f"{_GREEN}{line}{_RESET}"
    print(line, flush=True)


def fallback(failed: str, next_step: str) -> None:
    _prepare()
    print(f"{failed} failed, trying {next_step}", flush=True)


def note(message: str) -> None:
    _prepare()
    print(message, flush=True)


def _prepare() -> None:
    _enable_color()
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        return


def _use_color() -> bool:
    if os.environ.get("NO_COLOR"):
        return False
    return sys.stdout.isatty()


def _enable_color() -> None:
    global _READY
    if _READY or os.name != "nt":
        _READY = True
        return
    _READY = True
    try:
        import ctypes

        kernel = ctypes.windll.kernel32
        handle = kernel.GetStdHandle(-11)
        mode = ctypes.c_uint()
        if kernel.GetConsoleMode(handle, ctypes.byref(mode)):
            kernel.SetConsoleMode(handle, mode.value | 0x0004)
    except Exception:
        return
