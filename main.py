import random
import signal
import time
from typing import Any, Dict

from selenium.common.exceptions import WebDriverException

from src.browser import create_driver, load_cookies, save_cookies
from src.retweeter import TwitterRetweeter
from src.tracker import RetweetTracker
from src.utils import ensure_runtime_dirs, progress_bar, random_sleep, read_json, setup_logging, validate_config

RUNNING = True


def stop_handler(signum, frame):  # noqa: ANN001
    global RUNNING
    RUNNING = False


def enabled_items(items: list[Dict[str, Any]]) -> list[Dict[str, Any]]:
    return [item for item in items if item.get("enabled", True)]


def process_retweeter(
    account: Dict[str, Any],
    targets: list[Dict[str, Any]],
    settings: Dict[str, Any],
    tracker: RetweetTracker,
    logger,  # noqa: ANN001
    index: int,
    total: int,
) -> None:
    name = account["name"]
    driver = None
    progress_bar(index, total, f"checking {name}", enabled=settings.get("show_progress_bar", True))

    try:
        logger.info("Memulai akun retweeter %s/%s: %s", index, total, name)
        driver = create_driver(settings, account.get("proxy"), logger)
        if not load_cookies(driver, account["cookies_file"], logger, settings):
            logger.error("Lewati %s karena cookies tidak tersedia, rusak, expired, atau gagal dimuat", name)
            return

        bot = TwitterRetweeter(driver, settings, logger)
        if not bot.ensure_logged_in():
            logger.error("Lewati %s karena sesi login tidak valid", name)
            return

        for target in targets:
            if not RUNNING:
                break
            username = target["username"].lstrip("@")
            tweets = bot.latest_tweets(username, int(settings.get("max_latest_tweets_per_target", 3)))
            logger.info("Target @%s: menemukan %s tweet terbaru", username, len(tweets))
            for tweet in tweets:
                if not RUNNING:
                    break
                if tracker.has_retweeted(name, tweet["id"]):
                    logger.info("Skip tweet %s untuk %s karena sudah tercatat", tweet["id"], name)
                    continue
                if bot.retweet(tweet["url"]):
                    tracker.mark_retweeted(name, tweet["id"])

        if settings.get("save_cookies_after_run", True):
            save_cookies(driver, account["cookies_file"], logger)
    except RuntimeError as exc:
        logger.error("Runtime error saat memproses %s: %s", name, exc)
    except WebDriverException as exc:
        logger.error("Browser crash / WebDriver error pada %s: %s", name, exc)
    except Exception as exc:  # keep other accounts running if one account fails
        logger.exception("Error tidak terduga saat memproses %s: %s", name, exc)
    finally:
        if driver:
            try:
                driver.quit()
                logger.info("Browser ditutup untuk %s", name)
            except WebDriverException as exc:
                logger.warning("Browser untuk %s sudah tertutup atau gagal ditutup: %s", name, exc)


def wait_between_cycles(settings: Dict[str, Any], logger) -> None:  # noqa: ANN001
    delay_cfg = settings.get("check_delay_minutes", {"min": 40, "max": 90})
    delay_minutes = random.uniform(float(delay_cfg["min"]), float(delay_cfg["max"]))
    logger.info("Siklus selesai. Pengecekan berikutnya dalam %.1f menit. Tekan Ctrl+C untuk berhenti.", delay_minutes)
    remaining = delay_minutes * 60
    while RUNNING and remaining > 0:
        sleep_for = min(5, remaining)
        time.sleep(sleep_for)
        remaining -= sleep_for


def main() -> None:
    global RUNNING
    signal.signal(signal.SIGINT, stop_handler)
    signal.signal(signal.SIGTERM, stop_handler)

    accounts = read_json("config/accounts.json")
    settings = read_json("config/settings.json")
    ensure_runtime_dirs(settings)
    validate_config(accounts, settings)
    logger = setup_logging(settings.get("log_file", "logs/autoretweetx.log"), settings.get("console_colors", True))
    tracker = RetweetTracker(settings.get("retweet_history_path", "data/retweet_history.json"))

    targets = enabled_items(accounts["targets"])
    retweeters = enabled_items(accounts["retweeters"])
    logger.info("AutoretweetX aktif: %s target, %s retweeter", len(targets), len(retweeters))
    logger.info("Mode run_once: %s", "aktif" if settings.get("run_once", False) else "nonaktif")

    while RUNNING:
        total = len(retweeters)
        for index, account in enumerate(retweeters, start=1):
            if not RUNNING:
                break
            process_retweeter(account, targets, settings, tracker, logger, index, total)
            if RUNNING and index < total:
                cooldown = settings.get("account_cooldown_seconds", {"min": 8, "max": 20})
                random_sleep(
                    float(cooldown.get("min", 8)),
                    float(cooldown.get("max", 20)),
                    logger,
                    reason="Cooldown antar akun",
                )

        if settings.get("run_once", False):
            logger.info("run_once=true, script berhenti setelah 1 siklus.")
            break
        if RUNNING:
            wait_between_cycles(settings, logger)

    logger.info("AutoretweetX dihentikan dengan aman.")


if __name__ == "__main__":
    main()
