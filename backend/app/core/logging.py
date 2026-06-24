"""Logging configuration.

Forces UTF-8 on stdout/stderr so Hebrew + emoji never crash on a Windows
console (cp1255). Safe no-op where reconfigure is unavailable.
"""
import logging
import sys

_CONFIGURED = False


def setup_logging() -> None:
    global _CONFIGURED
    if _CONFIGURED:
        return
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure:
            try:
                reconfigure(encoding="utf-8", errors="replace")
            except Exception:  # noqa: BLE001
                pass
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s | %(message)s",
    )
    _CONFIGURED = True


# Configure on import so module-level logger usage is safe everywhere.
setup_logging()

logger = logging.getLogger("sadot")
