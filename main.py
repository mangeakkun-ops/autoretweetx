import random
import signal
from typing import Any, Dict

from src.browser import create_driver, load_cookies, save_cookies
from src.retweeter import TwitterRetweeter
from src.tracker import RetweetTracker
from src.utils import read_json, setup_logging, validate_config

RUNNING = True


def stop_handler(signum, frame):  # noqa: ANN001
    global RUNNING
    RUNNING = False


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
            return

        for target in targets:
            username = target["username"].lstrip("@")
            tweets = bot.latest_tweets(username, int(settings.get("max_latest_tweets_per_target", 3)))
            logger.info("Target @%s: menemukan %s tweet terbaru", username, len(tweets))
            for tweet in tweets:
                if tracker.has_retweeted(name, tweet["id"]):
                    logger.info("Skip tweet %s untuk %s karena sudah tercatat", tweet["id"], name)
                    continue
                if bot.retweet(tweet["url"]):
                    tracker.mark_retweeted(name, tweet["id"])

        save_cookies(driver, account["cookies_file"], logger)
    except Exception as exc:  # keep other accounts running if one account fails
        logger.exception("Error saat memproses %s: %s", name, exc)
    finally:
        if driver:
            driver.quit()
            logger.info("Browser ditutup untuk %s", name)


def main() -> None:
    global RUNNING
    signal.signal(signal.SIGINT, stop_handler)
    signal.signal(signal.SIGTERM, stop_handler)

    accounts = read_json("config/accounts.json")
    settings = read_json("config/settings.json")
    validate_config(accounts, settings)
    logger = setup_logging(settings.get("log_file", "logs/autoretweetx.log"))
    tracker = RetweetTracker(settings.get("retweet_history_path", "data/retweet_history.json"))

    targets = enabled_items(accounts["targets"])
    retweeters = enabled_items(accounts["retweeters"])
    logger.info("AutoretweetX aktif: %s target, %s retweeter", len(targets), len(retweeters))

    while RUNNING:
        for account in retweeters:
            if not RUNNING:
                break
            process_retweeter(account, targets, settings, tracker, logger)

        if not RUNNING:
            break

        delay_cfg = settings.get("check_delay_minutes", {"min": 40, "max": 90})
        delay_minutes = random.uniform(float(delay_cfg["min"]), float(delay_cfg["max"]))
        logger.info("Siklus selesai. Pengecekan berikutnya dalam %.1f menit. Tekan Ctrl+C untuk berhenti.", delay_minutes)
        remaining = delay_minutes * 60
        while RUNNING and remaining > 0:
            sleep_for = min(5, remaining)
            signal.pause() if False else __import__("time").sleep(sleep_for)
            remaining -= sleep_for

    logger.info("AutoretweetX dihentikan dengan aman.")


if __name__ == "__main__":
    main()
