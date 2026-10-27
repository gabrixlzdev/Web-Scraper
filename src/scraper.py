"""Module containing the core DynamicWebScraper class with Playwright automation."""

import os
import re
import time
from typing import Dict, List, Optional
from pathlib import Path
from urllib.parse import urljoin

# python-dotenv: Loads key-value pairs from .env into os.environ
from dotenv import load_dotenv

# Playwright Sync API: Synchronous browser automation methods
from playwright.sync_api import sync_playwright, Playwright, BrowserContext, Page, Locator

# Initialize environment variables
load_dotenv()


class DynamicWebScraper:
    """Production-grade scraper for extracting data from dynamic websites.

    Encapsulates persistent browser sessions, anti-detection configs,
    bot challenge handling, hybrid DOM/Regex extraction, and data storage.
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
        # Target search URL fallback
        self.target_url = target_url or os.getenv(
            "TARGET_URL", "https://www.zillow.com/austin-tx/"
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

        # launch_persistent_context retains cookies and session tokens in user_data_dir
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
        """Detects anti-bot verification screens (e.g. PerimeterX 'Press & Hold') and handles them."""
        if not self.page:
            return False

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
            return True

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

        print(f"[*] Waiting up to {wait_seconds}s for challenge clearance...")
        start_time = time.time()
        while time.time() - start_time < wait_seconds:
            if self.page.locator('article[data-test="property-card"], .photo-cards').count() > 0:
                print("[+] Bot challenge cleared! Active listings rendered.")
                return True
            time.sleep(1.5)

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
        """Simulates scrolling to trigger dynamic JavaScript lazy-loading.

        Scrolls the listing container pane directly via JavaScript to prevent
        unwanted map zooming.
        """
        if not self.page:
            return

        print(f"[*] Scrolling listings feed ({num_scrolls} steps) to hydrate lazy content...")
        for step in range(1, num_scrolls + 1):
            try:
                self.page.evaluate("""
                    () => {
                        const container = document.querySelector('#search-page-list-container') 
                                      || document.querySelector('[data-test="search-page-list-container"]')
                                      || document.querySelector('div[class*="search-page-list-container"]');
                        if (container) {
                            container.scrollBy({ top: 900, behavior: 'smooth' });
                        } else {
                            window.scrollBy({ top: 900, behavior: 'smooth' });
                        }
                    }
                """)
            except Exception:
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

    def _extract_card_data(self, card: Locator) -> Dict[str, Optional[str]]:
        """Extracts price, address, beds, baths, and listing URL using hybrid DOM + Regex strategy."""
        # --- 1. Address Extraction ---
        address = self._safe_get_text(card, [
            '[data-test="property-card-addr"]',
            'address[data-test="property-card-addr"]',
            'address',
            'a[data-test="property-card-link"]',
            'a[class*="StyledPropertyCardDataArea-anchor"]',
        ])

        # --- 2. Listing URL Extraction ---
        item_url = None
        link_selectors = [
            'a[data-test="property-card-link"]',
            'a[href*="/homedetails/"]',
            'a[href*="/b/"]',
            'a.property-card-link',
            'a[class*="StyledPropertyCardDataArea-anchor"]',
            'a[href]',
        ]
        for l_sel in link_selectors:
            try:
                link_elem = card.locator(l_sel).first
                if link_elem.count() > 0:
                    raw_href = link_elem.get_attribute("href")
                    if raw_href and raw_href.strip():
                        # Resolve relative links (e.g. /homedetails/...) to full absolute URLs
                        item_url = urljoin(self.target_url, raw_href.strip())
                        break
            except Exception:
                continue

        # --- 3. Price Extraction ---
        price = self._safe_get_text(card, [
            '[data-test="property-card-price"]',
            'span[data-test="property-card-price"]',
            'span[class*="StyledPrice"]',
            'div[class*="StyledPropertyCardDataArea-anchor"] span',
            'span:has-text("$")',
        ])

        # --- 4. Beds & Baths Extraction via DOM ---
        beds = self._safe_get_text(card, [
            'ul[class*="StyledPropertyCardHomeDetailsList"] li:has-text("bd")',
            'ul[class*="StyledPropertyCardHomeDetailsList"] li:has-text("bed")',
            'span:has-text("bd")',
            'span:has-text("bed")',
        ])

        baths = self._safe_get_text(card, [
            'ul[class*="StyledPropertyCardHomeDetailsList"] li:has-text("ba")',
            'ul[class*="StyledPropertyCardHomeDetailsList"] li:has-text("bath")',
            'span:has-text("ba")',
            'span:has-text("bath")',
        ])

        # --- 5. Fallback: Parse Card Inner Text with Regex ---
        try:
            raw_text = card.inner_text()
        except Exception:
            raw_text = ""

        if raw_text:
            # Price regex: matches currency symbols ($ € £ R$ C$ A$) followed by formatted digits
            if not price:
                price_match = re.search(
                    r"(?:\$|€|£|R\$|C\$|A\$)\s*\d{1,3}(?:[,\.]\d{3})*(?:\s*\/\s*(?:mo|month))?",
                    raw_text,
                )
                if price_match:
                    price = price_match.group(0).strip()

            # Beds regex: matches '3 bds', '2 beds', 'Studio', '4 bedrooms', etc.
            if not beds:
                beds_match = re.search(
                    r"(\d+(?:\.\d+)?|\bStudio\b)\s*(?:bds?|beds?|bedrooms?|dormitorio[s]?|quarto[s]?)",
                    raw_text,
                    re.IGNORECASE,
                )
                if beds_match:
                    beds = beds_match.group(0).strip()

            # Baths regex: matches '2 ba', '1.5 baths', '3 bathrooms', etc.
            if not baths:
                baths_match = re.search(
                    r"(\d+(?:\.\d+)?)\s*(?:ba|baths?|bathrooms?|baño[s]?|banheiro[s]?)",
                    raw_text,
                    re.IGNORECASE,
                )
                if baths_match:
                    baths = baths_match.group(0).strip()

            # Address regex fallback (if selector missed it)
            if not address:
                addr_match = re.search(
                    r"\d+[^,\n]+,\s*[^,\n]+,\s*[A-Z]{2}\s*\d{5}", raw_text
                )
                if addr_match:
                    address = addr_match.group(0).strip()

        return {
            "price": price,
            "address": address,
            "beds": beds,
            "baths": baths,
            "url": item_url,
        }

    def extract_listings(self, max_items: int = 20) -> List[Dict[str, Optional[str]]]:
        """Finds property cards on the page and extracts price, address, beds, baths, and URLs.

        Args:
            max_items: Upper limit of items to extract in a single pass.

        Returns:
            List of dictionaries containing extracted fields.
        """
        if not self.page:
            raise RuntimeError("Browser not started. Call start_browser() first.")

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
            record = self._extract_card_data(card)
            # Only record if at least address or price was detected (filters out ads)
            if record["price"] or record["address"]:
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
