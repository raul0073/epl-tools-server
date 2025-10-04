from __future__ import annotations
import time
from typing import Any, Tuple, Optional
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
import undetected_chromedriver as uc


class BrowserService:
    """
    Headless browser service for scraping websites like WhoScored.
    Uses undetected_chromedriver with stealth options.
    """

    def __init__(self, headless: bool = True, window_size: Tuple[int, int] = (1920, 1080)):
        self.headless = headless
        self.window_size = window_size
        self.driver = self._create_driver()

    def _create_driver(self) -> uc.Chrome:
        options = uc.ChromeOptions()
        options.add_argument(f"--window-size={self.window_size[0]},{self.window_size[1]}")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-extensions")
        options.add_argument("--ignore-certificate-errors")
        options.add_argument("--lang=en-US")
        options.add_argument("--disable-notifications")
        options.add_argument("--disable-infobars")
        if self.headless:
            # Use the new headless mode for Selenium 4.12+
            options.add_argument("--headless=new")

        try:
            driver = uc.Chrome(options=options)
            driver.set_page_load_timeout(30)
            return driver
        except WebDriverException as e:
            raise RuntimeError(f"Failed to start Chrome driver: {e}")

    def get_page(
        self,
        url: str,
        wait_for: Optional[str] = None,
        by: By = By.TAG_NAME,
        timeout: int = 15
    ) -> str:
        """
        Open a page and optionally wait for a specific element.
        :param url: URL to open
        :param wait_for: Optional CSS selector or element text to wait for
        :param by: Selenium By strategy
        :param timeout: Max wait seconds
        :return: Page HTML source
        """
        self.driver.get(url)
        if wait_for:
            try:
                WebDriverWait(self.driver, timeout).until(EC.presence_of_element_located((by, wait_for)))
            except TimeoutException:
                raise RuntimeError(f"Timeout waiting for element {wait_for} on {url}")
        return self.driver.page_source

    def find_elements(self, by: By, value: str) -> list:
        return self.driver.find_elements(by, value)

    def find_element(self, by: By, value: str) -> Any:
        return self.driver.find_element(by, value)

    def click_element(self, by: By, value: str, timeout: int = 10) -> None:
        element = WebDriverWait(self.driver, timeout).until(EC.element_to_be_clickable((by, value)))
        element.click()
        time.sleep(0.5)  # small delay for rendering

    def close(self) -> None:
        if hasattr(self, "driver") and self.driver:
            try:
                self.driver.quit()
            except Exception:
                pass
