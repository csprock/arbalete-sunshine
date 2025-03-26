import logging

def get_logger(name: str, level: int = logging.DEBUG, is_root=False) -> logging.Logger:

    fmt = "[%(levelname)s] %(name)s - %(asctime)s - %(module)s - %(funcName)s - %(lineno)d - %(message)s"
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