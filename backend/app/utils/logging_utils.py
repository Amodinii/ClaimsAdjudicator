import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from ..core.config import LOG_DIR

LOG_FILE = Path(LOG_DIR) / "app.log"

def setup_logging(level=logging.INFO):
    logger = logging.getLogger("plum")
    if logger.handlers:
        return logger 
    logger.setLevel(level)

    fmt = logging.Formatter(
        "%(asctime)s %(levelname)s [%(name)s:%(lineno)d] %(message)s"
    )

    ch = logging.StreamHandler()
    ch.setFormatter(fmt)
    logger.addHandler(ch)

    fh = RotatingFileHandler(LOG_FILE, maxBytes=5 * 1024 * 1024, backupCount=5)
    fh.setFormatter(fmt)
    logger.addHandler(fh)

    logging.getLogger("uvicorn").setLevel(logging.WARNING)
    return logger
