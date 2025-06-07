"""Logging utilities using the standard :mod:`logging` package."""
import logging
from config import LOG_LEVEL

_DEF_FORMAT = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"


def get_logger(name: str = __name__) -> logging.Logger:
    """Return a configured logger instance.

    Parameters
    ----------
    name:
        Name of the logger to retrieve.
    """
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter(_DEF_FORMAT))
        logger.addHandler(handler)
        logger.setLevel(LOG_LEVEL)
    return logger

# Example usage:
# from logging_utils import get_logger
# log = get_logger(__name__)
# log.info("Logger ready")
