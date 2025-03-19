import logging

def get_logger(name: str, level: int = logging.DEBUG, is_root=False) -> logging.Logger:

    fmt = "[%(levelnames)s] %(names)s - %(asctime)s - %(modules)s - %(funcNames)s - %(lineno)s - %(msg)s"
    datefmt = "%Y-%m-%dT%H:%M:%S%z"

    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.propagate = True

    if is_root:
        ch = logging.StreamHandler()
        ch.setLevel(level)
        ch.setFormatter(logging.Formatter(fmt=fmt, datefmt=datefmt))
        logger.addHandler(ch)

    return logger