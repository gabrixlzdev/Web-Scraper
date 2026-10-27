"""Module responsible for continuous infinite scrolling, pagination, and deduplication.

EDUCATIONAL NOTE:
Real estate platforms use a hybrid model:
1. Each page holds ~40 listings that load as you scroll down.
2. Once the 40th listing is reached, you must click the 'Next' button
   or advance the page parameter to access the next batch of 40 listings.
This module combines container scrolling with multi-page navigation.
"""

import json
import time
import urllib.parse
from typing import Dict, List, Optional, Set
from playwright.sync_api import Page
from src.extractor import ListingExtractor


class InfiniteScroller:
    """Coordinates container scrolling and multi-page pagination for high-volume extraction."""

    def __init__(self, page: Page, extractor: ListingExtractor) -> None:
        self.page = page
        self.extractor = extractor

    def scroll_container(self, scroll_amount: int = 1000) -> bool:
        """Scrolls the listings container down using JavaScript.

        Why JavaScript evaluate?
        Directly calling element.scrollBy() in the browser's JavaScript engine prevents
        the mouse wheel from accidentally zooming the map instead of scrolling the list.
        """
        try:
            return bool(
                self.page.evaluate(f"""
                    () => {{
                        const container = document.querySelector('#search-page-list-container')
                                      || document.querySelector('[data-test="search-page-list-container"]')
                                      || document.querySelector('div[class*="search-page-list-container"]');
                        if (container) {{
                            const prev = container.scrollTop;
                            container.scrollBy({{ top: {scroll_amount}, behavior: 'smooth' }});
                            return true;
                        }}
                        window.scrollBy({{ top: {scroll_amount}, behavior: 'smooth' }});
                        return true;
                    }}
                """)
            )
        except Exception:
            self.page.mouse.wheel(0, scroll_amount)
            return True

    def go_to_next_page(self, next_page_num: int) -> bool:
        """Navigates to the next page of listings.

        Strategy 1: Find and click the 'Next' pagination button in the DOM.
        Strategy 2: If the button is obscured or missing, advance the page parameter in the URL.
        """
        print(f"[*] Attempting to advance to Page {next_page_num}...")

        # --- Strategy 1: Click the 'Next' button ---
        next_button_selectors = [
            'a[rel="next"]',
            'a[title="Next page"]',
            'button[title="Next page"]',
            'nav[aria-label="Pagination"] a[aria-label="Next page"]',
            'li.PaginationNumberItem-next a',
        ]

        for sel in next_button_selectors:
            try:
                btn = self.page.locator(sel).first
                # is_visible() checks if the element is rendered and not hidden
                if btn.count() > 0 and btn.is_visible(timeout=2000):
                    print(f"[+] Found Next Page button via '{sel}'. Clicking...")
                    # Scroll into view so click doesn't miss
                    btn.scroll_into_view_if_needed()
                    btn.click()
                    # Wait 3 seconds for new cards to render in the DOM
                    time.sleep(3)
                    return True
            except Exception:
                continue

        # --- Strategy 2: URL Pagination Fallback ---
        # If the button couldn't be clicked, update the URL directly:
        current_url = self.page.url
        print(f"[*] Button click unavailable. Attempting URL pagination for Page {next_page_num}...")

        try:
            parsed = urllib.parse.urlparse(current_url)
            query_dict = urllib.parse.parse_qs(parsed.query)

            # Case A: URL uses searchQueryState JSON (like state search URLs)
            if "searchQueryState" in query_dict:
                state_json_str = query_dict["searchQueryState"][0]
                state_data = json.loads(state_json_str)
                # Inject or update pagination page number
                state_data["pagination"] = {"currentPage": next_page_num}
                query_dict["searchQueryState"] = [json.dumps(state_data)]
                new_query = urllib.parse.urlencode(query_dict, doseq=True)
                next_url = urllib.parse.urlunparse(parsed._replace(query=new_query))

            # Case B: Standard URL (e.g. /austin-tx/ -> /austin-tx/2_p/)
            else:
                base_path = parsed.path.rstrip("/")
                # Replace existing _p tag or append new one
                import re
                if re.search(r"\/\d+_p$", base_path):
                    new_path = re.sub(r"\/\d+_p$", f"/{next_page_num}_p", base_path)
                else:
                    new_path = f"{base_path}/{next_page_num}_p"
                next_url = urllib.parse.urlunparse(parsed._replace(path=new_path))

            print(f"[*] Navigating directly to Next Page URL: {next_url}")
            self.page.goto(next_url, wait_until="domcontentloaded", timeout=30000)
            time.sleep(3)
            return True

        except Exception as e:
            print(f"[!] URL pagination fallback failed: {e}")
            return False

    def extract_with_infinite_scroll(
        self,
        target_count: int = 50,
        max_scroll_attempts: int = 15,
        max_pages: int = 25,
        scroll_delay: float = 1.2,
    ) -> List[Dict[str, Optional[str]]]:
        """Collects listings by scrolling each page and advancing across multiple pages.

        Args:
            target_count: Total unique listings desired (0 or negative = Unlimited).
            max_scroll_attempts: Number of scroll passes per page to load all ~40 cards.
            max_pages: Safety limit on total pages to traverse.
            scroll_delay: Seconds to wait for dynamic JavaScript hydration after each scroll.
        """
        results: List[Dict[str, Optional[str]]] = []
        seen_keys: Set[str] = set()
        is_unlimited = target_count <= 0

        target_display = "UNLIMITED" if is_unlimited else str(target_count)
        print(f"[*] Starting Multi-Page Extraction (Target: {target_display} unique listings)...")

        for current_page in range(1, max_pages + 1):
            print(f"\n--- [Page {current_page}/{max_pages}] Scanning listings ---")
            consecutive_empty_scrolls = 0

            # Scroll through the listings on the CURRENT page
            for scroll_step in range(1, max_scroll_attempts + 1):
                cards = self.extractor.find_cards(self.page)
                if not cards:
                    time.sleep(scroll_delay)
                    continue

                dom_count = cards.count()
                new_in_scroll = 0

                # Extract each card in the DOM
                for i in range(dom_count):
                    card = cards.nth(i)
                    record = self.extractor.extract_single_card(card)

                    unique_key = record.get("url") or record.get("address")
                    if not unique_key:
                        continue

                    # Deduplication check
                    if unique_key not in seen_keys:
                        seen_keys.add(unique_key)
                        results.append(record)
                        new_in_scroll += 1

                        # Stop if fixed target is met
                        if not is_unlimited and len(results) >= target_count:
                            print(f"\n[+] Successfully reached target of {target_count} unique listings!")
                            return results

                target_str = "UNLIMITED" if is_unlimited else f"{len(results)}/{target_count}"
                print(
                    f"  [P.{current_page} Scroll {scroll_step:02d}/{max_scroll_attempts}] "
                    f"Total Collected: {len(results)} (Target: {target_str}) | "
                    f"New: +{new_in_scroll}"
                )

                # If no new cards appear for 3 consecutive scrolls, current page is fully loaded
                if new_in_scroll == 0:
                    consecutive_empty_scrolls += 1
                    if consecutive_empty_scrolls >= 3:
                        print(f"  [*] Current Page {current_page} fully loaded.")
                        break
                else:
                    consecutive_empty_scrolls = 0

                # Scroll container down to reveal more cards
                self.scroll_container(scroll_amount=1000)
                time.sleep(scroll_delay)

            # Check if we have met the target before advancing pages
            if not is_unlimited and len(results) >= target_count:
                break

            # Advance to the next page!
            has_next = self.go_to_next_page(next_page_num=current_page + 1)
            if not has_next:
                print("[*] Reached last available page or could not advance. Finishing extraction.")
                break

        print(f"\n[+] Extraction complete! Gathered {len(results)} total unique listings across pages.")
        return results
