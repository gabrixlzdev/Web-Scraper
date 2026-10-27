"""Module containing the core DynamicWebScraper class with Playwright automation."""

import os
import time
from typing import Dict, List, Optional
from pathlib import Path

# python-dotenv: Loads key-value pairs from .env into os.environ
from dotenv import load_dotenv

# Playwright Sync API: Synchronous browser automation methods
from playwright.sync_api import sync_playwright, Playwright, BrowserContext, Page, Locator

# Initialize environment variables
load_dotenv()


class DynamicWebScraper:
    """Production-grade scraper for extracting data from dynamic websites.

    Encapsulates persistent browser sessions, anti-detection configs,
    bot challenge handling, DOM extraction, and data storage.
    """

    def __init__(
        self,
        target_url: Optional[str] = None,
        headless: Optional[bool] = None,
        timeout: Optional[int] = None,
        user_agent: Optional[str] = None,
        output_dir: str = "data",
        user_data_dir: Optional[str] = None,
    ) -> None:
        """Initializes scraper settings and establishes instance variables."""
        # Target search URL
        self.target_url = target_url or os.getenv(
            "TARGET_URL", "https://www.zillow.com/homes/for_sale/"
        )

        # Headless mode: True = background; False = visual window
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

        # Directory where browser session cookies/cache persist across runs
        profile_path = user_data_dir or os.getenv("USER_DATA_DIR", "browser_profile")
        self.user_data_dir = Path(profile_path)
        self.user_data_dir.mkdir(parents=True, exist_ok=True)

        # In-memory storage for extracted records
        self.raw_listings: List[Dict[str, Optional[str]]] = []

        # Playwright lifecycle handles
        self._playwright: Optional[Playwright] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None

    def start_browser(self) -> None:
        """Launches a persistent browser context to retain cookies and bypass bot detection."""
        self._playwright = sync_playwright().start()

        # launch_persistent_context keeps cookies, cache, and session state on disk.
        # This makes the browser look like a returning human user rather than a brand-new bot.
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

        # A persistent context automatically creates an initial tab:
        if self.context.pages:
            self.page = self.context.pages[0]
        else:
            self.page = self.context.new_page()

        self.page.set_default_timeout(self.timeout)

    def handle_bot_challenge(self, wait_seconds: int = 15) -> bool:
        """Detects anti-bot verification screens (e.g. PerimeterX 'Press & Hold') and handles them.

        1. First tries an automated mouse press-and-hold (mouse down, sleep 6s, mouse up).
        2. If a manual puzzle or hold is still needed, gives the user a grace window in the visual window.
        3. Once solved, cookies are saved to browser_profile/ forever.
        """
        if not self.page:
            return False

        # Known PerimeterX / DataDome / Cloudflare challenge selectors
        challenge_selectors = [
            '#px-captcha',
            'div[id*="captcha"]',
            'button:has-text("Press & Hold")',
            'div:has-text("Press & Hold")',
            'iframe[title*="challenge"]',
        ]

        found_challenge = False
        target_element: Optional[Locator] = None

        for sel in challenge_selectors:
            try:
                loc = self.page.locator(sel).first
                if loc.is_visible(timeout=2000):
                    found_challenge = True
                    target_element = loc
                    print(f"[!] Bot challenge detected via selector: '{sel}'")
                    break
            except Exception:
                continue

        if not found_challenge:
            # No challenge detected; page is clean
            return True

        # Attempt automated press-and-hold
        if target_element:
            try:
                box = target_element.bounding_box()
                if box:
                    center_x = box["x"] + (box["width"] / 2)
                    center_y = box["y"] + (box["height"] / 2)
                    print("[*] Attempting automated mouse Press-and-Hold for 6 seconds...")
                    self.page.mouse.move(center_x, center_y)
                    self.page.mouse.down()
                    time.sleep(6)
                    self.page.mouse.up()
                    time.sleep(2)
            except Exception as e:
                print(f"[!] Automated hold simulation failed: {e}")

        # Check if challenge is now cleared
        print(f"[*] Waiting up to {wait_seconds}s for challenge clearance...")
        start_time = time.time()
        while time.time() - start_time < wait_seconds:
            # Check if property cards or page content have loaded
            if self.page.locator('article[data-test="property-card"], .photo-cards').count() > 0:
                print("[+] Bot challenge cleared! Active listings rendered.")
                return True

            # If still on challenge, wait a bit
            time.sleep(1.5)

        print("[!] Warning: Challenge may still be active. Proceeding to extraction attempt.")
        return False

    def navigate(self, url: Optional[str] = None) -> bool:
        """Navigates to the specified URL or target_url and checks for bot challenges."""
        dest_url = url or self.target_url
        if not self.page:
            raise RuntimeError("Browser not started. Call start_browser() first or use 'with' block.")

        try:
            print(f"[*] Navigating to: {dest_url}")
            self.page.goto(dest_url, wait_until="domcontentloaded", timeout=self.timeout)

            # Check and handle any anti-bot screens
            self.handle_bot_challenge()
            return True
        except Exception as e:
            print(f"[!] Navigation error to {dest_url}: {e}")
            return False

    def scroll_page(self, num_scrolls: int = 3, delay: float = 1.2) -> None:
        """Simulates human scrolling to trigger dynamic JavaScript lazy-loading."""
        if not self.page:
            return

        print(f"[*] Scrolling page ({num_scrolls} steps) to hydrate lazy content...")
        for step in range(1, num_scrolls + 1):
            self.page.mouse.wheel(0, 800)
            time.sleep(delay)

    def _safe_get_text(self, parent: Locator, selectors: List[str]) -> Optional[str]:
        """Tries multiple fallback CSS/XPath selectors and extracts the first valid text."""
        for selector in selectors:
            try:
                elem = parent.locator(selector).first
                if elem.count() > 0:
                    text = elem.inner_text().strip()
                    if text:
                        return text
            except Exception:
                continue
        return None

    def extract_listings(self, max_items: int = 20) -> List[Dict[str, Optional[str]]]:
        """Finds property cards on the page and extracts price, address, beds, and baths."""
        if not self.page:
            raise RuntimeError("Browser not started. Call start_browser() first.")

        # Candidate selectors for property card containers
        card_selectors = [
            'article[data-test="property-card"]',
            'div[data-test="property-card"]',
            'ul.photo-cards > li',
            'div[class*="StyledPropertyCardDataWrapper"]',
            '.list-card',
        ]

        cards_locator = None
        for selector in card_selectors:
            loc = self.page.locator(selector)
            if loc.count() > 0:
                cards_locator = loc
                print(f"[+] Located {loc.count()} listing cards using selector: '{selector}'")
                break

        if not cards_locator or cards_locator.count() == 0:
            print("[!] No listing cards found on the active page.")
            return []

        total_available = cards_locator.count()
        extract_count = min(total_available, max_items)
        print(f"[*] Extracting details from {extract_count} listings...")

        extracted: List[Dict[str, Optional[str]]] = []

        for index in range(extract_count):
            card = cards_locator.nth(index)

            # 1. Price
            price = self._safe_get_text(card, [
                '[data-test="property-card-price"]',
                'span[data-test="property-card-price"]',
                'span[class*="StyledPrice"]',
                'div[class*="StyledPropertyCardDataArea-anchor"] span',
            ])

            # 2. Address
            address = self._safe_get_text(card, [
                '[data-test="property-card-addr"]',
                'address[data-test="property-card-addr"]',
                'address',
                'a[data-test="property-card-link"]',
            ])

            # 3. Beds
            beds = self._safe_get_text(card, [
                'ul[class*="StyledPropertyCardHomeDetailsList"] li:has-text("bd")',
                'ul[class*="StyledPropertyCardHomeDetailsList"] li:has-text("bed")',
                'span:has-text("bd")',
                'span:has-text("bed")',
            ])

            # 4. Baths
            baths = self._safe_get_text(card, [
                'ul[class*="StyledPropertyCardHomeDetailsList"] li:has-text("ba")',
                'ul[class*="StyledPropertyCardHomeDetailsList"] li:has-text("bath")',
                'span:has-text("ba")',
                'span:has-text("bath")',
            ])

            record = {
                "price": price,
                "address": address,
                "beds": beds,
                "baths": baths,
            }

            extracted.append(record)

        self.raw_listings.extend(extracted)
        return extracted

    def close_browser(self) -> None:
        """Safely shuts down Context and Playwright driver."""
        if self.page:
            self.page = None
        if self.context:
            self.context.close()
            self.context = None
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
