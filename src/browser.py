"""Browser lifecycle management module using Playwright."""

import os
from pathlib import Path
from typing import Optional, Tuple
from playwright.sync_api import sync_playwright, Playwright, BrowserContext, Page


class BrowserManager:
    """Manages browser startup, persistent cookies/profiles, and shutdown."""

    def __init__(
        self,
        headless: bool = False,
        timeout: int = 30000,
        user_agent: Optional[str] = None,
        user_data_dir: str = "browser_profile",
    ) -> None:
        # Whether the browser runs hidden (True) or visible on screen (False)
        self.headless = headless
        # Maximum time in milliseconds before page operations time out
        self.timeout = timeout
        # Realistic Chrome user agent string to prevent automated bot blocks
        self.user_agent = (
            user_agent
            or os.getenv("USER_AGENT")
            or "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        )
        # Folder on disk where session cookies and cache are saved
        self.user_data_dir = Path(user_data_dir)
        self.user_data_dir.mkdir(parents=True, exist_ok=True)

        # Internal Playwright references (set to None until launch)
        self._playwright: Optional[Playwright] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None

    def launch(self) -> Tuple[BrowserContext, Page]:
        """Starts Chromium with persistent session cookies and anti-bot flags."""
        # Start the underlying Playwright engine process
        self._playwright = sync_playwright().start()

        # Launch persistent browser context (saves cookies in user_data_dir)
        self.context = self._playwright.chromium.launch_persistent_context(
            user_data_dir=str(self.user_data_dir.resolve()),
            headless=self.headless,
            user_agent=self.user_agent,
            viewport={"width": 1920, "height": 1080},  # Desktop 1080p resolution
            locale="en-US",                             # Standard US locale
            timezone_id="America/New_York",
            args=[
                "--disable-blink-features=AutomationControlled",  # Masks navigator.webdriver
                "--start-maximized",                             # Opens window maximized
            ],
        )

        # Grab the existing default tab or create a new one
        if self.context.pages:
            self.page = self.context.pages[0]
        else:
            self.page = self.context.new_page()

        # Apply timeout to all clicks, navigations, and waits
        self.page.set_default_timeout(self.timeout)
        return self.context, self.page

    def close(self) -> None:
        """Safely shuts down the browser and releases system resources."""
        if self.page:
            self.page = None
        if self.context:
            self.context.close()
            self.context = None
        if self._playwright:
            self._playwright.stop()
            self._playwright = None
