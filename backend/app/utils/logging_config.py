import logging
import logging.handlers
from pathlib import Path


def setup_logging(log_dir: Path = Path("logs"), level: int = logging.INFO) -> None:
    log_dir.mkdir(exist_ok=True)

    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s:%(funcName)s:%(lineno)d | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    app_handler = logging.handlers.RotatingFileHandler(
        log_dir / "application.log",
        maxBytes=5_242_880,
        backupCount=3,
        encoding="utf-8",
    )
    app_handler.setLevel(level)
    app_handler.setFormatter(formatter)

    error_handler = logging.handlers.RotatingFileHandler(
        log_dir / "error.log",
        maxBytes=5_242_880,
        backupCount=3,
        encoding="utf-8",
    )
    error_handler.setLevel(logging.WARNING)
    error_handler.setFormatter(formatter)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    root_logger.addHandler(app_handler)
    root_logger.addHandler(error_handler)
    root_logger.addHandler(console_handler)
