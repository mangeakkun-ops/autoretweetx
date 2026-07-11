import logging
import re
from typing import Any, Dict, List

from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from src.utils import random_sleep

STATUS_RE = re.compile(r"/status/(\d+)")


class TwitterRetweeter:
    def __init__(self, driver: WebDriver, settings: Dict[str, Any], logger: logging.Logger):
        self.driver = driver
        self.settings = settings
        self.logger = logger
        self.wait = WebDriverWait(driver, 20)

    def ensure_logged_in(self) -> bool:
        self.driver.get("https://x.com/home")
        try:
            self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "a[href='/home'], [data-testid='SideNav_AccountSwitcher_Button']")))
            return True
        except TimeoutException:
            self.logger.warning("Login belum terdeteksi. Pastikan cookies masih valid.")
            return False

    def latest_tweets(self, target_username: str, limit: int) -> List[Dict[str, str]]:
        username = target_username.lstrip("@")
        self.driver.get(f"https://x.com/{username}")
        try:
            self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "article[data-testid='tweet']")))
        except TimeoutException:
            self.logger.warning("Tidak menemukan tweet untuk target @%s", username)
            return []

        tweets: List[Dict[str, str]] = []
        for article in self.driver.find_elements(By.CSS_SELECTOR, "article[data-testid='tweet']"):
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
        return tweets

    def retweet(self, tweet_url: str) -> bool:
        self.driver.get(tweet_url)
        try:
            retweet_button = self.wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "[data-testid='retweet']")))
        except TimeoutException:
            if self.driver.find_elements(By.CSS_SELECTOR, "[data-testid='unretweet']"):
                self.logger.info("Tweet sudah dalam status retweeted: %s", tweet_url)
                return True
            self.logger.warning("Tombol retweet tidak ditemukan: %s", tweet_url)
            return False

        retweet_button.click()
        self._action_delay()
        try:
            confirm = self.wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "[data-testid='retweetConfirm']")))
            confirm.click()
            self._action_delay()
            self.logger.info("Retweet berhasil: %s", tweet_url)
            return True
        except TimeoutException:
            self.logger.warning("Dialog konfirmasi retweet tidak muncul: %s", tweet_url)
            return False

    def _action_delay(self) -> None:
        delay = self.settings.get("action_delay_seconds", {"min": 2, "max": 6})
        random_sleep(float(delay.get("min", 2)), float(delay.get("max", 6)))
