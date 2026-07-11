import json
import logging
from pathlib import Path
from typing import Any, Dict, List

import undetected_chromedriver as uc
from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.remote.webdriver import WebDriver
from selenium_stealth import stealth

X_HOME_URL = "https://x.com/home"
X_BASE_URL = "https://x.com"


def create_driver(settings: Dict[str, Any], proxy: str | None = None, logger: logging.Logger | None = None) -> WebDriver:
    attempts = int(settings.get("retry", {}).get("browser_start_attempts", 2))
    last_error: Exception | None = None

    for attempt in range(1, attempts + 1):
        try:
            options = uc.ChromeOptions()
            if settings.get("headless", False):
                options.add_argument("--headless=new")
            options.add_argument(f"--window-size={settings.get('browser_window_size', '1280,900')}")
            options.add_argument("--disable-blink-features=AutomationControlled")
            options.add_argument("--disable-notifications")
            options.add_argument("--disable-popup-blocking")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--no-first-run")
            options.add_argument("--no-default-browser-check")
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
        except WebDriverException as exc:
            last_error = exc
            if logger:
                logger.warning("Gagal membuka browser (percobaan %s/%s): %s", attempt, attempts, exc)

    raise RuntimeError(f"Browser gagal dibuka setelah {attempts} percobaan") from last_error


def safe_get(driver: WebDriver, url: str, logger: logging.Logger, refresh_attempts: int = 1) -> bool:
    for attempt in range(0, refresh_attempts + 1):
        try:
            driver.get(url)
            return True
        except TimeoutException:
            logger.warning("Timeout saat membuka %s (percobaan %s)", url, attempt + 1)
        except WebDriverException as exc:
            logger.error("Browser error saat membuka %s: %s", url, exc)
            return False
    return False


def load_cookies(driver: WebDriver, cookies_file: str, logger: logging.Logger, settings: Dict[str, Any] | None = None) -> bool:
    path = Path(cookies_file)
    if not path.exists():
        logger.error("Cookie file belum ada: %s", path)
        return False

    refresh_attempts = int((settings or {}).get("retry", {}).get("page_refresh_attempts", 1))
    if not safe_get(driver, X_BASE_URL, logger, refresh_attempts):
        return False

    try:
        with path.open("r", encoding="utf-8") as file:
            cookies: List[Dict[str, Any]] = json.load(file)
    except json.JSONDecodeError as exc:
        logger.error("Format JSON cookies tidak valid di %s: %s", path, exc)
        return False

    if not isinstance(cookies, list) or not cookies:
        logger.error("Cookie file kosong atau bukan list JSON: %s", path)
        return False

    loaded = 0
    for cookie in cookies:
        if not isinstance(cookie, dict) or not cookie.get("name") or "value" not in cookie:
            continue
        prepared = cookie.copy()
        prepared.pop("sameSite", None)
        if "expirationDate" in prepared and "expiry" not in prepared:
            prepared["expiry"] = int(prepared.pop("expirationDate"))
        try:
            driver.add_cookie(prepared)
            loaded += 1
        except WebDriverException as exc:
            logger.debug("Cookie dilewati (%s): %s", prepared.get("name"), exc)

    if loaded == 0:
        logger.error("Tidak ada cookie yang berhasil dimuat dari %s", path)
        return False

    logger.info("Berhasil memuat %s cookie dari %s", loaded, path)
    return safe_get(driver, X_HOME_URL, logger, refresh_attempts)


def save_cookies(driver: WebDriver, cookies_file: str, logger: logging.Logger) -> None:
    path = Path(cookies_file)
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with path.open("w", encoding="utf-8") as file:
            json.dump(driver.get_cookies(), file, ensure_ascii=False, indent=2)
            file.write("\n")
        logger.info("Cookies tersimpan ke %s", path)
    except WebDriverException as exc:
        logger.warning("Gagal membaca cookies dari browser: %s", exc)
    except OSError as exc:
        logger.warning("Gagal menyimpan cookies ke %s: %s", path, exc)
