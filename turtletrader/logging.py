import logging, os


def get_logger(name: str = "turtle"):
    level = os.getenv("TURTLE_LOG_LEVEL", "INFO").upper()
    fmt = os.getenv("TURTLE_LOG_FMT", "%(asctime)s %(levelname)s %(name)s: %(message)s")
    datefmt = os.getenv("TURTLE_LOG_DATEFMT", "%H:%M:%S")
    logger = logging.getLogger(name)
    if not logger.handlers:
        h = logging.StreamHandler()
        h.setFormatter(logging.Formatter(fmt=fmt, datefmt=datefmt))
        logger.addHandler(h)
    logger.setLevel(level)
    return logger
