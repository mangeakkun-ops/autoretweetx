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


def create_driver(settings: Dict[str, Any], proxy: str | None = None) -> WebDriver:
    options = uc.ChromeOptions()
    if settings.get("headless", False):
        options.add_argument("--headless=new")
    options.add_argument(f"--window-size={settings.get('browser_window_size', '1280,900')}")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--disable-notifications")
    options.add_argument("--disable-popup-blocking")
    options.add_argument("--no-first-run")
    options.add_argument("--no-default-browser-check")
    options.add_argument("--lang=en-US")
    if settings.get("disable_gpu", True):
        options.add_argument("--disable-gpu")
    if proxy:
        options.add_argument(f"--proxy-server={proxy}")

    try:
        driver = uc.Chrome(options=options, use_subprocess=True)
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
        raise RuntimeError(
            "Browser gagal dibuat. Pastikan Google Chrome terinstall, versi Chrome kompatibel, "
            "dan proxy (jika dipakai) valid."
        ) from exc


def _normalize_cookie(cookie: Dict[str, Any]) -> Dict[str, Any]:
    normalized = cookie.copy()
    allowed_keys = {"name", "value", "domain", "path", "expiry", "secure", "httpOnly"}
    if "expirationDate" in normalized and "expiry" not in normalized:
        normalized["expiry"] = int(normalized.pop("expirationDate"))
    normalized.pop("sameSite", None)
    normalized.setdefault("path", "/")
    return {key: value for key, value in normalized.items() if key in allowed_keys and value is not None}


def load_cookies(driver: WebDriver, cookies_file: str, logger: logging.Logger) -> bool:
    path = Path(cookies_file)
    if not path.exists():
        logger.warning("Cookie file belum ada: %s", path)
        return False

    try:
        driver.get(X_BASE_URL)
        with path.open("r", encoding="utf-8") as file:
            cookies: List[Dict[str, Any]] = json.load(file)
    except json.JSONDecodeError as exc:
        logger.error("Cookie file bukan JSON valid: %s (%s)", path, exc)
        return False
    except (OSError, TimeoutException, WebDriverException) as exc:
        logger.error("Gagal membuka X atau membaca cookies %s: %s", path, exc)
        return False

    loaded = 0
    for raw_cookie in cookies:
        try:
            cookie = _normalize_cookie(raw_cookie)
            if not cookie.get("name") or "value" not in cookie:
                continue
            driver.add_cookie(cookie)
            loaded += 1
        except WebDriverException as exc:
            logger.debug("Cookie dilewati karena format/domain tidak cocok: %s", exc)

    if loaded == 0:
        logger.warning("Tidak ada cookie yang berhasil dimuat dari %s", path)
        return False

    logger.info("Berhasil memuat %s cookie dari %s", loaded, path)
    try:
        driver.get(X_HOME_URL)
    except (TimeoutException, WebDriverException) as exc:
        logger.warning("Cookies dimuat, tetapi halaman home gagal dibuka: %s", exc)
        return False
    return True


def save_cookies(driver: WebDriver, cookies_file: str, logger: logging.Logger) -> None:
    path = Path(cookies_file)
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with path.open("w", encoding="utf-8") as file:
            json.dump(driver.get_cookies(), file, ensure_ascii=False, indent=2)
            file.write("\n")
        logger.info("Cookies tersimpan ke %s", path)
    except (OSError, WebDriverException) as exc:
        logger.warning("Gagal menyimpan cookies ke %s: %s", path, exc)
