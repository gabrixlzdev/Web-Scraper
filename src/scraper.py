"""High-level scraper orchestrator module."""

import os
from typing import Dict, List, Optional
from pathlib import Path
from dotenv import load_dotenv

from src.browser import BrowserManager
from src.bot_handler import BotChallengeHandler
from src.extractor import ListingExtractor
from src.scroller import InfiniteScroller

# Load variables from local .env into os.environ
load_dotenv()


class DynamicWebScraper:
    """Orchestrator coordinating browser, bot defense, extractor, and scroller."""

    def __init__(
        self,
        target_url: Optional[str] = None,
        headless: Optional[bool] = None,
        timeout: Optional[int] = None,
        user_agent: Optional[str] = None,
        output_dir: str = "data",
        user_data_dir: Optional[str] = None,
    ) -> None:
        # Resolve target URL from argument or .env
        self.target_url = target_url or os.getenv("TARGET_URL", "https://www.zillow.com/austin-tx/")

        # Headless mode: True = hidden in background, False = visual window
        if headless is not None:
            self.headless = headless
        else:
            env_headless = os.getenv("HEADLESS", "False").strip().lower()
            self.headless = env_headless in ("true", "1", "yes")

        # Milliseconds timeout for operations (clicks, navigation)
        self.timeout = timeout or int(os.getenv("SCRAPER_TIMEOUT", "30000"))
        # Output directory where CSV/JSON files are saved
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        # Persistent profile directory storing cookies across runs
        profile_path = user_data_dir or os.getenv("USER_DATA_DIR", "browser_profile")

        # Initialize sub-components
        self.browser_manager = BrowserManager(
            headless=self.headless,
            timeout=self.timeout,
            user_agent=user_agent,
            user_data_dir=profile_path,
        )
        self.extractor = ListingExtractor(base_url=self.target_url)
        self.bot_handler: Optional[BotChallengeHandler] = None
        self.scroller: Optional[InfiniteScroller] = None

        self.context = None
        self.page = None
        self.raw_listings: List[Dict[str, Optional[str]]] = []

    def start_browser(self) -> None:
        """Launches Chromium and initializes bot handler and scroller components."""
        self.context, self.page = self.browser_manager.launch()
        self.bot_handler = BotChallengeHandler(page=self.page)
        self.scroller = InfiniteScroller(page=self.page, extractor=self.extractor)

    def navigate(self, url: Optional[str] = None) -> bool:
        """Navigates to URL and clears any bot verification challenges."""
        dest_url = url or self.target_url
        if not self.page:
            raise RuntimeError("Browser not started. Call start_browser() first or use 'with' block.")

        try:
            print(f"[*] Navigating to: {dest_url}")
            self.page.goto(dest_url, wait_until="domcontentloaded", timeout=self.timeout)
            if self.bot_handler:
                self.bot_handler.resolve_challenge()
            return True
        except Exception as e:
            print(f"[!] Navigation error to {dest_url}: {e}")
            return False

    def extract_listings(
        self,
        target_count: int = 50,
        max_scroll_attempts: int = 15,
        max_pages: int = 25,
    ) -> List[Dict[str, Optional[str]]]:
        """Extracts listings across multiple pages until target_count is reached."""
        if not self.scroller:
            raise RuntimeError("Scraper not initialized. Call start_browser() first.")

        listings = self.scroller.extract_with_infinite_scroll(
            target_count=target_count,
            max_scroll_attempts=max_scroll_attempts,
            max_pages=max_pages,
        )
        self.raw_listings.extend(listings)
        return listings

    def close_browser(self) -> None:
        """Closes browser session cleanly."""
        self.browser_manager.close()

    def __enter__(self) -> "DynamicWebScraper":
        """Starts browser automatically upon entering a 'with' block."""
        self.start_browser()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Guarantees browser is closed upon exiting a 'with' block."""
        self.close_browser()


# Backwards compatibility alias
RealEstateScraper = DynamicWebScraper
