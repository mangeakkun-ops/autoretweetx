import logging
import re
from typing import Any, Dict, List

from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from src.browser import safe_get
from src.utils import random_sleep

STATUS_RE = re.compile(r"/status/(\d+)")


class TwitterRetweeter:
    def __init__(self, driver: WebDriver, settings: Dict[str, Any], logger: logging.Logger):
        self.driver = driver
        self.settings = settings
        self.logger = logger
        timeout = int(settings.get("element_wait_timeout_seconds", 20))
        self.wait = WebDriverWait(driver, timeout)

    def ensure_logged_in(self) -> bool:
        if not safe_get(self.driver, "https://x.com/home", self.logger, self._refresh_attempts()):
            return False
        try:
            self.wait.until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, "a[href='/home'], [data-testid='SideNav_AccountSwitcher_Button']")
                )
            )
            return True
        except TimeoutException:
            self.logger.error("Login belum terdeteksi. Cookies mungkin expired, salah akun, atau X meminta verifikasi.")
            return False
        except WebDriverException as exc:
            self.logger.error("Browser bermasalah saat validasi login: %s", exc)
            return False

    def latest_tweets(self, target_username: str, limit: int) -> List[Dict[str, str]]:
        username = target_username.lstrip("@")
        if not safe_get(self.driver, f"https://x.com/{username}", self.logger, self._refresh_attempts()):
            return []
        try:
            self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "article[data-testid='tweet']")))
        except TimeoutException:
            self.logger.warning("Tidak menemukan tweet untuk target @%s. Akun bisa private, kosong, atau layout X berubah.", username)
            return []
        except WebDriverException as exc:
            self.logger.error("Browser error saat membaca target @%s: %s", username, exc)
            return []

        tweets: List[Dict[str, str]] = []
        try:
            articles = self.driver.find_elements(By.CSS_SELECTOR, "article[data-testid='tweet']")
            for article in articles:
                links = article.find_elements(By.CSS_SELECTOR, "a[href*='/status/']")
                for link in links:
                    href = link.get_attribute("href") or ""
                    match = STATUS_RE.search(href)
                    if match:
                        tweet_id = match.group(1)
                        if not any(item["id"] == tweet_id for item in tweets):
                            tweets.append({"id": tweet_id, "url": href, "target": username})
                        break
                if len(tweets) >= limit:
                    break
        except WebDriverException as exc:
            self.logger.error("Gagal parsing tweet target @%s: %s", username, exc)
        return tweets

    def retweet(self, tweet_url: str) -> bool:
        if not safe_get(self.driver, tweet_url, self.logger, self._refresh_attempts()):
            return False
        try:
            retweet_button = self.wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "[data-testid='retweet']")))
        except TimeoutException:
            try:
                if self.driver.find_elements(By.CSS_SELECTOR, "[data-testid='unretweet']"):
                    self.logger.info("Tweet sudah dalam status retweeted: %s", tweet_url)
                    return True
            except WebDriverException:
                pass
            self.logger.warning("Tombol retweet tidak ditemukan: %s", tweet_url)
            return False
        except WebDriverException as exc:
            self.logger.error("Browser error saat mencari tombol retweet: %s", exc)
            return False

        try:
            retweet_button.click()
            self._action_delay()
            confirm = self.wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "[data-testid='retweetConfirm']")))
            confirm.click()
            self._action_delay()
            self.logger.info("Retweet berhasil: %s", tweet_url)
            return True
        except TimeoutException:
            self.logger.warning("Dialog konfirmasi retweet tidak muncul: %s", tweet_url)
            return False
        except WebDriverException as exc:
            self.logger.error("Gagal melakukan retweet %s: %s", tweet_url, exc)
            return False

    def _action_delay(self) -> None:
        delay = self.settings.get("action_delay_seconds", {"min": 2, "max": 6})
        random_sleep(float(delay.get("min", 2)), float(delay.get("max", 6)))

    def _refresh_attempts(self) -> int:
        return int(self.settings.get("retry", {}).get("page_refresh_attempts", 1))
