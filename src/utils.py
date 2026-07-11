import json
import logging
import random
import sys
import time
from pathlib import Path
from typing import Any, Dict

try:
    from colorama import Fore, Style, init as colorama_init
except ModuleNotFoundError:  # graceful fallback before dependencies are installed
    class _NoColor:
        BLACK = RED = GREEN = YELLOW = BLUE = MAGENTA = CYAN = WHITE = RESET_ALL = ""
        BRIGHT = DIM = NORMAL = ""

    Fore = Style = _NoColor()

    def colorama_init(*args: Any, **kwargs: Any) -> None:
        return None


class ColorFormatter(logging.Formatter):
    COLORS = {
        logging.DEBUG: Style.DIM,
        logging.INFO: Fore.CYAN,
        logging.WARNING: Fore.YELLOW,
        logging.ERROR: Fore.RED,
        logging.CRITICAL: Fore.RED + Style.BRIGHT,
    }

    def __init__(self, *args: Any, use_colors: bool = True, **kwargs: Any):
        super().__init__(*args, **kwargs)
        self.use_colors = use_colors

    def format(self, record: logging.LogRecord) -> str:
        message = super().format(record)
        if not self.use_colors:
            return message
        color = self.COLORS.get(record.levelno, "")
        return f"{color}{message}{Style.RESET_ALL}"


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


def ensure_runtime_dirs(settings: Dict[str, Any]) -> None:
    Path(settings.get("log_file", "logs/autoretweetx.log")).parent.mkdir(parents=True, exist_ok=True)
    Path(settings.get("retweet_history_path", "data/retweet_history.json")).parent.mkdir(parents=True, exist_ok=True)
    Path("config/cookies").mkdir(parents=True, exist_ok=True)


def setup_logging(log_file: str, use_colors: bool = True) -> logging.Logger:
    colorama_init(autoreset=True)
    Path(log_file).parent.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger("autoretweetx")
    logger.setLevel(logging.INFO)
    logger.handlers.clear()

    log_format = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
    date_format = "%Y-%m-%d %H:%M:%S"

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(ColorFormatter(log_format, datefmt=date_format, use_colors=use_colors))
    logger.addHandler(console_handler)

    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setFormatter(logging.Formatter(log_format, datefmt=date_format))
    logger.addHandler(file_handler)
    return logger


def random_sleep(min_seconds: float, max_seconds: float, logger: logging.Logger | None = None, reason: str = "Menunggu") -> None:
    duration = random.uniform(min_seconds, max_seconds)
    if logger:
        logger.info("%s %.1f detik", reason, duration)
    time.sleep(duration)


def progress_bar(current: int, total: int, label: str, width: int = 28, enabled: bool = True) -> None:
    if not enabled or total <= 0:
        return
    filled = int(width * current / total)
    bar = "█" * filled + "░" * (width - filled)
    percent = int(100 * current / total)
    print(f"\r{Fore.GREEN}[{bar}] {current}/{total} ({percent}%) {label}{Style.RESET_ALL}", end="", flush=True)
    if current >= total:
        print()


def validate_config(accounts: Dict[str, Any], settings: Dict[str, Any]) -> None:
    if not isinstance(accounts.get("targets"), list) or not accounts["targets"]:
        raise ValueError("config/accounts.json harus memiliki list targets minimal 1 akun")
    if not isinstance(accounts.get("retweeters"), list) or not accounts["retweeters"]:
        raise ValueError("config/accounts.json harus memiliki list retweeters minimal 1 akun")
    delay = settings.get("check_delay_minutes", {})
    if delay.get("min", 0) > delay.get("max", 0):
        raise ValueError("settings.check_delay_minutes.min tidak boleh lebih besar dari max")
    action_delay = settings.get("action_delay_seconds", {})
    if action_delay.get("min", 0) > action_delay.get("max", 0):
        raise ValueError("settings.action_delay_seconds.min tidak boleh lebih besar dari max")
