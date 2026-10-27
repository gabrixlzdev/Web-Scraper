"""High-level scraper orchestrator module."""

# Standard library modules
import os
from typing import Dict, List, Optional
from pathlib import Path
# Load environment settings from .env file
from dotenv import load_dotenv

# Import decoupled internal components
from src.browser import BrowserManager
from src.bot_handler import BotChallengeHandler
from src.extractor import ListingExtractor
from src.scroller import InfiniteScroller

# Execute load_dotenv to load .env settings into os.environ
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
        # Fallback to TARGET_URL from .env or default city URL
        self.target_url = target_url or os.getenv("TARGET_URL", "https://www.zillow.com/austin-tx/")

        # Headless setting: True = invisible in background; False = visible on screen
        if headless is not None:
            self.headless = headless
        else:
            env_headless = os.getenv("HEADLESS", "False").strip().lower()
            self.headless = env_headless in ("true", "1", "yes")

        # Network/element wait timeout in milliseconds (default 30 seconds)
        self.timeout = timeout or int(os.getenv("SCRAPER_TIMEOUT", "30000"))

        # Local folder where CSV output spreadsheets are stored
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Local folder where browser cookies and session tokens are saved
        profile_path = user_data_dir or os.getenv("USER_DATA_DIR", "browser_profile")

        # Initialize the browser lifecycle manager
        self.browser_manager = BrowserManager(
            headless=self.headless,
            timeout=self.timeout,
            user_agent=user_agent,
            user_data_dir=profile_path,
        )

        # Initialize the card extractor with the target base URL
        self.extractor = ListingExtractor(base_url=self.target_url)

        # Bot challenge handler and scroller are initialized when the browser starts
        self.bot_handler: Optional[BotChallengeHandler] = None
        self.scroller: Optional[InfiniteScroller] = None

        # BrowserContext and active Page handles
        self.context = None
        self.page = None

        # In-memory list accumulating all extracted listings
        self.raw_listings: List[Dict[str, Optional[str]]] = []

    def start_browser(self) -> None:
        """Launches Chromium and initializes bot handler and scroller components."""
        # Start Chromium through BrowserManager
        self.context, self.page = self.browser_manager.launch()
        # Initialize bot challenge detector with the active browser tab
        self.bot_handler = BotChallengeHandler(page=self.page)
        # Initialize scroller with active tab and extractor
        self.scroller = InfiniteScroller(page=self.page, extractor=self.extractor)

    def navigate(self, url: Optional[str] = None) -> bool:
        """Navigates to URL and clears any bot verification challenges."""
        dest_url = url or self.target_url
        if not self.page:
            raise RuntimeError("Browser not started. Call start_browser() first or use 'with' block.")

        try:
            print(f"[*] Navigating to: {dest_url}")
            # Navigate to the target page and wait until initial DOM structure is loaded
            self.page.goto(dest_url, wait_until="domcontentloaded", timeout=self.timeout)

            # Check if an anti-bot challenge overlay appeared and resolve it
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

        # Delegate continuous scrolling and page traversal to InfiniteScroller
        listings = self.scroller.extract_with_infinite_scroll(
            target_count=target_count,
            max_scroll_attempts=max_scroll_attempts,
            max_pages=max_pages,
        )
        # Accumulate records into the scraper instance
        self.raw_listings.extend(listings)
        return listings

    def close_browser(self) -> None:
        """Closes browser session cleanly."""
        self.browser_manager.close()

    def __enter__(self) -> "DynamicWebScraper":
        """Runs automatically when entering a Python 'with' block."""
        self.start_browser()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Runs automatically when leaving a 'with' block (ensures browser always closes)."""
        self.close_browser()


# Backwards compatibility alias
RealEstateScraper = DynamicWebScraper
