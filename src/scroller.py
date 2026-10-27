"""Infinite scrolling, multi-page pagination, and deduplication module."""

import json
import time
import urllib.parse
from typing import Dict, List, Optional, Set
from playwright.sync_api import Page
from src.extractor import ListingExtractor


class InfiniteScroller:
    """Manages continuous container scrolling and multi-page pagination."""

    def __init__(self, page: Page, extractor: ListingExtractor) -> None:
        self.page = page
        self.extractor = extractor

    def scroll_container(self, scroll_amount: int = 1000) -> bool:
        """Scrolls the specific listings container down using JavaScript.

        Calling element.scrollBy() directly inside the browser avoids zooming the map.
        """
        try:
            return bool(
                self.page.evaluate(f"""
                    () => {{
                        const container = document.querySelector('#search-page-list-container')
                                      || document.querySelector('[data-test="search-page-list-container"]')
                                      || document.querySelector('div[class*="search-page-list-container"]');
                        if (container) {{
                            container.scrollBy({{ top: {scroll_amount}, behavior: 'smooth' }});
                            return true;
                        }}
                        window.scrollBy({{ top: {scroll_amount}, behavior: 'smooth' }});
                        return true;
                    }}
                """)
            )
        except Exception:
            # Fallback to mouse wheel if container evaluation fails
            self.page.mouse.wheel(0, scroll_amount)
            return True

    def go_to_next_page(self, next_page_num: int) -> bool:
        """Navigates to the next page of listings via Next button click or URL update."""
        print(f"[*] Attempting to advance to Page {next_page_num}...")

        # 1. Strategy A: Try clicking the Next Page button in the DOM
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
                if btn.count() > 0 and btn.is_visible(timeout=2000):
                    print(f"[+] Found Next Page button via '{sel}'. Clicking...")
                    btn.scroll_into_view_if_needed()
                    btn.click()
                    # Wait 3 seconds for new listings to render
                    time.sleep(3)
                    return True
            except Exception:
                continue

        # 2. Strategy B: URL Fallback (updates page number in current URL)
        current_url = self.page.url
        print(f"[*] Button click unavailable. Navigating via URL parameter to Page {next_page_num}...")

        try:
            parsed = urllib.parse.urlparse(current_url)
            query_dict = urllib.parse.parse_qs(parsed.query)

            # Check if URL uses searchQueryState JSON
            if "searchQueryState" in query_dict:
                state_json_str = query_dict["searchQueryState"][0]
                state_data = json.loads(state_json_str)
                # Inject next page into JSON parameter
                state_data["pagination"] = {"currentPage": next_page_num}
                query_dict["searchQueryState"] = [json.dumps(state_data)]
                new_query = urllib.parse.urlencode(query_dict, doseq=True)
                next_url = urllib.parse.urlunparse(parsed._replace(query=new_query))
            else:
                # Standard URL: append or replace /2_p/ in path
                base_path = parsed.path.rstrip("/")
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
        """Collects unique listings across pages using infinite scrolling and pagination."""
        results: List[Dict[str, Optional[str]]] = []
        seen_keys: Set[str] = set()
        is_unlimited = target_count <= 0

        target_display = "UNLIMITED" if is_unlimited else str(target_count)
        print(f"[*] Starting Multi-Page Extraction (Target: {target_display} unique listings)...")

        # Iterate page by page
        for current_page in range(1, max_pages + 1):
            print(f"\n--- [Page {current_page}/{max_pages}] Scanning listings ---")
            consecutive_empty_scrolls = 0

            # Scroll through the listings on the current page
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

                    # Deduplication: only add if we haven't seen this URL/address yet
                    if unique_key not in seen_keys:
                        seen_keys.add(unique_key)
                        results.append(record)
                        new_in_scroll += 1

                        # Stop if user's fixed target is reached
                        if not is_unlimited and len(results) >= target_count:
                            print(f"\n[+] Successfully reached target of {target_count} unique listings!")
                            return results

                target_str = "UNLIMITED" if is_unlimited else f"{len(results)}/{target_count}"
                print(
                    f"  [P.{current_page} Scroll {scroll_step:02d}/{max_scroll_attempts}] "
                    f"Total Collected: {len(results)} (Target: {target_str}) | "
                    f"New: +{new_in_scroll}"
                )

                # Stop scrolling this page if no new items appear for 3 scrolls
                if new_in_scroll == 0:
                    consecutive_empty_scrolls += 1
                    if consecutive_empty_scrolls >= 3:
                        print(f"  [*] Current Page {current_page} fully loaded.")
                        break
                else:
                    consecutive_empty_scrolls = 0

                # Scroll container down
                self.scroll_container(scroll_amount=1000)
                time.sleep(scroll_delay)

            # Check if target is met before advancing to next page
            if not is_unlimited and len(results) >= target_count:
                break

            # Advance to the next page
            has_next = self.go_to_next_page(next_page_num=current_page + 1)
            if not has_next:
                print("[*] Reached last available page or could not advance. Finishing extraction.")
                break

        print(f"\n[+] Extraction complete! Gathered {len(results)} total unique listings across pages.")
        return results
