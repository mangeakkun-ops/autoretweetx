import json
import logging
import random
import sys
import time
from pathlib import Path
from typing import Any, Dict

from colorama import Fore, Style, init as colorama_init


class ColorFormatter(logging.Formatter):
    COLORS = {
        logging.DEBUG: Fore.CYAN,
        logging.INFO: Fore.GREEN,
        logging.WARNING: Fore.YELLOW,
        logging.ERROR: Fore.RED,
        logging.CRITICAL: Fore.MAGENTA,
    }

    def format(self, record: logging.LogRecord) -> str:
        message = super().format(record)
        color = self.COLORS.get(record.levelno, "")
        return f"{color}{message}{Style.RESET_ALL}" if color else message


def ensure_runtime_dirs(*paths: str | Path) -> None:
    for path in paths:
        Path(path).mkdir(parents=True, exist_ok=True)


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


def setup_logging(log_file: str, colored_console: bool = True) -> logging.Logger:
    colorama_init(autoreset=True)
    Path(log_file).parent.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger("autoretweetx")
    logger.setLevel(logging.INFO)
    logger.handlers.clear()

    plain_formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    console_formatter: logging.Formatter = ColorFormatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    ) if colored_console else plain_formatter

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setFormatter(plain_formatter)
    logger.addHandler(file_handler)
    return logger


def print_progress(current: int, total: int, label: str = "Progress") -> None:
    total = max(total, 1)
    current = min(current, total)
    width = 24
    filled = int(width * current / total)
    bar = "█" * filled + "░" * (width - filled)
    percent = int(100 * current / total)
    end = "\n" if current >= total else "\r"
    print(f"{Fore.CYAN}{label}: [{bar}] {current}/{total} ({percent}%){Style.RESET_ALL}", end=end, flush=True)


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
    if float(delay.get("min", 0)) > float(delay.get("max", 0)):
        raise ValueError("settings.check_delay_minutes.min tidak boleh lebih besar dari max")

    action_delay = settings.get("action_delay_seconds", {})
    if float(action_delay.get("min", 0)) > float(action_delay.get("max", 0)):
        raise ValueError("settings.action_delay_seconds.min tidak boleh lebih besar dari max")

    account_pause = settings.get("per_account_pause_seconds", {"min": 0, "max": 0})
    if float(account_pause.get("min", 0)) > float(account_pause.get("max", 0)):
        raise ValueError("settings.per_account_pause_seconds.min tidak boleh lebih besar dari max")

    if int(settings.get("max_latest_tweets_per_target", 1)) < 1:
        raise ValueError("settings.max_latest_tweets_per_target minimal 1")
