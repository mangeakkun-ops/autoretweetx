import json
import logging
import random
import sys
import time
from pathlib import Path
from typing import Any, Dict


def read_json(path: str | Path, default: Any | None = None) -> Any:
    file_path = Path(path)
    if not file_path.exists():
        if default is not None:
            return default
        raise FileNotFoundError(f"File tidak ditemukan: {file_path}")
    with file_path.open("r", encoding="utf-8") as file:
        return json.load(file)


def write_json(path: str | Path, data: Any) -> None:
    file_path = Path(path)
    file_path.parent.mkdir(parents=True, exist_ok=True)
    with file_path.open("w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=2)
        file.write("\n")


def setup_logging(log_file: str) -> logging.Logger:
    Path(log_file).parent.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger("autoretweetx")
    logger.setLevel(logging.INFO)
    logger.handlers.clear()

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    return logger


def random_sleep(min_seconds: float, max_seconds: float, logger: logging.Logger | None = None) -> None:
    duration = random.uniform(min_seconds, max_seconds)
    if logger:
        logger.info("Menunggu %.1f detik", duration)
    time.sleep(duration)


def validate_config(accounts: Dict[str, Any], settings: Dict[str, Any]) -> None:
    if not isinstance(accounts.get("targets"), list) or not accounts["targets"]:
        raise ValueError("config/accounts.json harus memiliki list targets minimal 1 akun")
    if not isinstance(accounts.get("retweeters"), list) or not accounts["retweeters"]:
        raise ValueError("config/accounts.json harus memiliki list retweeters minimal 1 akun")
    delay = settings.get("check_delay_minutes", {})
    if delay.get("min", 0) > delay.get("max", 0):
        raise ValueError("settings.check_delay_minutes.min tidak boleh lebih besar dari max")
