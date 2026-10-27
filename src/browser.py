"""Module responsible for Playwright browser lifecycle and persistent sessions.

EDUCATIONAL NOTE:
Separating browser management into its own module follows the Single Responsibility
Principle. It ensures that changes to browser arguments, proxy configs, or user-agents
do not affect extraction or bot-bypass logic.
"""

import os
from pathlib import Path
from typing import Optional, Tuple
from playwright.sync_api import sync_playwright, Playwright, BrowserContext, Page


class BrowserManager:
    """Manages Playwright initialization, persistent profiles, and safe shutdown."""

    def __init__(
        self,
        headless: bool = False,
        timeout: int = 30000,
        user_agent: Optional[str] = None,
        user_data_dir: str = "browser_profile",
    ) -> None:
        self.headless = headless
        self.timeout = timeout
        self.user_agent = (
            user_agent
            or os.getenv("USER_AGENT")
            or "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        )
        self.user_data_dir = Path(user_data_dir)
        self.user_data_dir.mkdir(parents=True, exist_ok=True)

        self._playwright: Optional[Playwright] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None

    def launch(self) -> Tuple[BrowserContext, Page]:
        """Starts Playwright and returns an active persistent BrowserContext and Page."""
        self._playwright = sync_playwright().start()

        self.context = self._playwright.chromium.launch_persistent_context(
            user_data_dir=str(self.user_data_dir.resolve()),
            headless=self.headless,
            user_agent=self.user_agent,
            viewport={"width": 1920, "height": 1080},
            locale="en-US",
            timezone_id="America/New_York",
            args=[
                "--disable-blink-features=AutomationControlled",  # Masks navigator.webdriver
                "--start-maximized",
            ],
        )

        if self.context.pages:
            self.page = self.context.pages[0]
        else:
            self.page = self.context.new_page()

        self.page.set_default_timeout(self.timeout)
        return self.context, self.page

    def close(self) -> None:
        """Safely cleans up context and terminates Playwright."""
        if self.page:
            self.page = None
        if self.context:
            self.context.close()
            self.context = None
        if self._playwright:
            self._playwright.stop()
            self._playwright = None
