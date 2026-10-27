"""Module containing the core DynamicWebScraper class with Playwright automation."""

import os
import time
from typing import Dict, List, Optional
from pathlib import Path

# python-dotenv: Loads key-value pairs from .env into os.environ
from dotenv import load_dotenv

# Playwright Sync API: Provides synchronous methods to control browser instances
from playwright.sync_api import sync_playwright, Playwright, Browser, BrowserContext, Page

# Initialize environment variables
load_dotenv()


class DynamicWebScraper:
    """Production-grade scraper for extracting data from dynamic websites.

    Encapsulates Playwright lifecycle management, anti-detection configs,
    and data storage.
    """

    def __init__(
        self,
        target_url: Optional[str] = None,
        headless: Optional[bool] = None,
        timeout: Optional[int] = None,
        user_agent: Optional[str] = None,
        output_dir: str = "data",
    ) -> None:
        """Initializes scraper settings and establishes instance variables."""
        # Target URL fallback
        self.target_url = target_url or os.getenv("TARGET_URL", "https://www.zillow.com")

        # Headless mode: True = hidden background execution; False = visual window
        if headless is not None:
            self.headless = headless
        else:
            env_headless = os.getenv("HEADLESS", "False").strip().lower()
            self.headless = env_headless in ("true", "1", "yes")

        # Timeout in milliseconds (default 30 seconds)
        if timeout is not None:
            self.timeout = timeout
        else:
            self.timeout = int(os.getenv("SCRAPER_TIMEOUT", "30000"))

        # User-Agent header string mimicking a standard modern desktop browser
        self.user_agent = (
            user_agent
            or os.getenv("USER_AGENT")
            or "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        )

        # Output folder for data artifacts
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # In-memory storage for extracted records
        self.raw_listings: List[Dict[str, Optional[str]]] = []

        # Playwright lifecycle handles (initialized as None until browser starts)
        self._playwright: Optional[Playwright] = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None

    def start_browser(self) -> None:
        """Launches the Chromium engine and creates an anti-detection browser context."""
        # Start the underlying Playwright driver process
        self._playwright = sync_playwright().start()

        # Launch Chromium (headless=False will physically open the browser window)
        self.browser = self._playwright.chromium.launch(
            headless=self.headless,
            args=[
                "--disable-blink-features=AutomationControlled",  # Disables navigator.webdriver flag
                "--start-maximized",                             # Starts window maximized
            ],
        )

        # Create an isolated browser context with custom viewport, locale, and user agent
        self.context = self.browser.new_context(
            user_agent=self.user_agent,
            viewport={"width": 1920, "height": 1080},
            locale="en-US",
            timezone_id="America/New_York",
        )

        # Create a new tab (Page) inside our configured context
        self.page = self.context.new_page()
        # Set default timeout for all page operations (clicks, waits, navigation)
        self.page.set_default_timeout(self.timeout)

    def navigate(self, url: Optional[str] = None) -> bool:
        """Navigates the browser page to the specified URL or target_url.

        Returns:
            True if navigation succeeded, False otherwise.
        """
        dest_url = url or self.target_url
        if not self.page:
            raise RuntimeError("Browser not started. Call start_browser() first or use 'with' block.")

        try:
            print(f"[*] Navigating to: {dest_url}")
            # wait_until='domcontentloaded': Waits for the basic HTML/DOM structure to load
            self.page.goto(dest_url, wait_until="domcontentloaded", timeout=self.timeout)
            return True
        except Exception as e:
            print(f"[!] Navigation error to {dest_url}: {e}")
            return False

    def close_browser(self) -> None:
        """Safely shuts down Page, Context, Browser, and Playwright driver."""
        # Close in reverse order of creation to prevent hanging processes
        if self.page:
            self.page.close()
            self.page = None
        if self.context:
            self.context.close()
            self.context = None
        if self.browser:
            self.browser.close()
            self.browser = None
        if self._playwright:
            self._playwright.stop()
            self._playwright = None

    def __enter__(self) -> "DynamicWebScraper":
        """Allows using the scraper with Python's 'with' statement."""
        self.start_browser()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Ensures browser resources are cleanly closed on exit or exception."""
        self.close_browser()


# Backwards compatibility alias
RealEstateScraper = DynamicWebScraper
