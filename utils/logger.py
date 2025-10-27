import logging
from typing import Optional

def get_logger(name: Optional[str] = None, level: int = logging.INFO) -> logging.Logger:
    """
    Return a module logger configured with a StreamHandler and a compact formatter.
    Safe to call multiple times (won't add duplicate handlers).
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    # avoid adding multiple handlers in environments that reload modules
    if not any(isinstance(h, logging.StreamHandler) for h in logger.handlers):
        handler = logging.StreamHandler()
        handler.setLevel(level)
        handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s"))
        logger.addHandler(handler)
        logger.propagate = False
    return logger