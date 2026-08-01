import logging
import sys

def setup_logging(log_level: str = "INFO") -> logging.Logger:
    logger = logging.getLogger("graphguard")
    logger.setLevel(log_level.upper())

    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            fmt="[%(asctime)s] [%(levelname)s] [%(name)s] [ReqID: %(request_id)s] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger

logger = setup_logging()
