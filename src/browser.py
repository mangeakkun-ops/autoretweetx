import json
import logging
from pathlib import Path
from typing import Any, Dict, List

import undetected_chromedriver as uc
from selenium.webdriver.remote.webdriver import WebDriver
from selenium_stealth import stealth

X_HOME_URL = "https://x.com/home"
X_BASE_URL = "https://x.com"


def create_driver(settings: Dict[str, Any], proxy: str | None = None) -> WebDriver:
    options = uc.ChromeOptions()
    if settings.get("headless", False):
        options.add_argument("--headless=new")
    options.add_argument(f"--window-size={settings.get('browser_window_size', '1280,900')}")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--disable-notifications")
    options.add_argument("--lang=en-US")
    if proxy:
        options.add_argument(f"--proxy-server={proxy}")

    driver = uc.Chrome(options=options)
    driver.set_page_load_timeout(int(settings.get("page_load_timeout_seconds", 45)))
    stealth(
        driver,
        languages=["en-US", "en"],
        vendor="Google Inc.",
        platform="Win32",
        webgl_vendor="Intel Inc.",
        renderer="Intel Iris OpenGL Engine",
        fix_hairline=True,
    )
    return driver


def load_cookies(driver: WebDriver, cookies_file: str, logger: logging.Logger) -> bool:
    path = Path(cookies_file)
    if not path.exists():
        logger.warning("Cookie file belum ada: %s", path)
        return False

    driver.get(X_BASE_URL)
    with path.open("r", encoding="utf-8") as file:
        cookies: List[Dict[str, Any]] = json.load(file)

    loaded = 0
    for cookie in cookies:
        cookie = cookie.copy()
        cookie.pop("sameSite", None)
        if "expirationDate" in cookie and "expiry" not in cookie:
            cookie["expiry"] = int(cookie.pop("expirationDate"))
        try:
            driver.add_cookie(cookie)
            loaded += 1
        except Exception as exc:  # cookie formats exported by extensions can vary
            logger.debug("Cookie dilewati: %s", exc)

    logger.info("Berhasil memuat %s cookie dari %s", loaded, path)
    driver.get(X_HOME_URL)
    return loaded > 0


def save_cookies(driver: WebDriver, cookies_file: str, logger: logging.Logger) -> None:
    path = Path(cookies_file)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as file:
        json.dump(driver.get_cookies(), file, ensure_ascii=False, indent=2)
        file.write("\n")
    logger.info("Cookies tersimpan ke %s", path)
