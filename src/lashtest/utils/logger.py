import logging

logging.getLogger("lashtest").addHandler(logging.NullHandler())

def get_logger() -> logging.Logger:
    """Get a logger for the lashtest library."""
    return logging.getLogger("lashtest")