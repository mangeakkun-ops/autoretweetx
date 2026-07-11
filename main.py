import argparse
import random
import signal
import time
from typing import Any, Dict

from selenium.common.exceptions import WebDriverException

from src.browser import create_driver, load_cookies, save_cookies
from src.retweeter import TwitterRetweeter
from src.tracker import RetweetTracker
from src.utils import ensure_runtime_dirs, print_progress, random_sleep, read_json, setup_logging, validate_config

RUNNING = True


def stop_handler(signum, frame):  # noqa: ANN001
    global RUNNING
    RUNNING = False


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="AutoretweetX - automation retweet berbasis Selenium dan cookies per akun.",
    )
    parser.add_argument(
        "--once",
        "--test",
        action="store_true",
        help="Jalankan satu siklus saja untuk testing/debugging, lalu berhenti.",
    )
    return parser.parse_args()


def enabled_items(items: list[Dict[str, Any]]) -> list[Dict[str, Any]]:
    return [item for item in items if item.get("enabled", True)]


def process_retweeter(account: Dict[str, Any], targets: list[Dict[str, Any]], settings: Dict[str, Any], tracker: RetweetTracker, logger) -> None:  # noqa: ANN001
    name = account["name"]
    driver = None
    try:
        logger.info("Memulai akun retweeter: %s", name)
        driver = create_driver(settings, account.get("proxy"))
        if not load_cookies(driver, account["cookies_file"], logger):
            logger.warning("Lewati %s karena cookies tidak tersedia/valid", name)
            return

        bot = TwitterRetweeter(driver, settings, logger)
        if not bot.ensure_logged_in():
            save_cookies(driver, account["cookies_file"], logger)
            logger.warning("Lewati %s karena sesi login tidak valid", name)
            return

        total_targets = len(targets)
        for index, target in enumerate(targets, start=1):
            username = target["username"].lstrip("@")
            print_progress(index, total_targets, f"Checking @{username}")
            tweets = bot.latest_tweets(username, int(settings.get("max_latest_tweets_per_target", 3)))
            logger.info("Target @%s: menemukan %s tweet terbaru", username, len(tweets))
            for tweet in tweets:
                if tracker.has_retweeted(name, tweet["id"]):
                    logger.info("Skip tweet %s untuk %s karena sudah tercatat", tweet["id"], name)
                    continue
                if bot.retweet(tweet["url"]):
                    tracker.mark_retweeted(name, tweet["id"])

        save_cookies(driver, account["cookies_file"], logger)
    except WebDriverException as exc:
        logger.exception("Browser crash saat memproses %s. Akun lain tetap dilanjutkan: %s", name, exc)
    except Exception as exc:  # keep other accounts running if one account fails
        logger.exception("Error saat memproses %s: %s", name, exc)
    finally:
        if driver:
            try:
                driver.quit()
                logger.info("Browser ditutup untuk %s", name)
            except WebDriverException as exc:
                logger.warning("Browser untuk %s sudah tertutup/tidak merespons: %s", name, exc)


def main() -> None:
    global RUNNING
    args = parse_args()
    signal.signal(signal.SIGINT, stop_handler)
    signal.signal(signal.SIGTERM, stop_handler)

    ensure_runtime_dirs("logs", "data", "config/cookies")
    accounts = read_json("config/accounts.json")
    settings = read_json("config/settings.json")
    validate_config(accounts, settings)
    logger = setup_logging(settings.get("log_file", "logs/autoretweetx.log"), bool(settings.get("colored_console", True)))
    tracker = RetweetTracker(settings.get("retweet_history_path", "data/retweet_history.json"))

    targets = enabled_items(accounts["targets"])
    retweeters = enabled_items(accounts["retweeters"])
    run_once = bool(settings.get("run_once", False) or args.once)
    logger.info("AutoretweetX aktif: %s target, %s retweeter, run_once=%s", len(targets), len(retweeters), run_once)

    while RUNNING:
        for account in retweeters:
            if not RUNNING:
                break
            process_retweeter(account, targets, settings, tracker, logger)
            pause_cfg = settings.get("per_account_pause_seconds", {"min": 3, "max": 8})
            if RUNNING and account != retweeters[-1]:
                random_sleep(float(pause_cfg.get("min", 3)), float(pause_cfg.get("max", 8)), logger)

        if run_once:
            logger.info("Mode run_once aktif. Script berhenti setelah satu siklus.")
            break
        if not RUNNING:
            break

        delay_cfg = settings.get("check_delay_minutes", {"min": 40, "max": 90})
        delay_minutes = random.uniform(float(delay_cfg["min"]), float(delay_cfg["max"]))
        logger.info("Siklus selesai. Pengecekan berikutnya dalam %.1f menit. Tekan Ctrl+C untuk berhenti.", delay_minutes)
        remaining = delay_minutes * 60
        while RUNNING and remaining > 0:
            sleep_for = min(5, remaining)
            time.sleep(sleep_for)
            remaining -= sleep_for

    logger.info("AutoretweetX dihentikan dengan aman.")


if __name__ == "__main__":
    main()
