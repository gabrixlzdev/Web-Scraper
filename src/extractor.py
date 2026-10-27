"""Module responsible for extracting property details using hybrid DOM + Regex strategy.

EDUCATIONAL NOTE:
Extractors convert raw, noisy HTML into clean, structured dictionaries.
By decoupling extraction from navigation, this module can be tested in isolation
or adapted for completely different target websites with minimal effort.
"""

import re
from typing import Dict, List, Optional
from urllib.parse import urljoin
from playwright.sync_api import Locator, Page


class ListingExtractor:
    """Extracts price, address, beds, baths, and direct URLs from listing cards."""

    def __init__(self, base_url: str) -> None:
        self.base_url = base_url

    def find_cards(self, page: Page) -> Optional[Locator]:
        """Locates property card containers on the active page."""
        card_selectors = [
            'article[data-test="property-card"]',
            'div[data-test="property-card"]',
            'ul.photo-cards > li',
            'div[class*="StyledPropertyCardDataWrapper"]',
            '.list-card',
        ]
        for sel in card_selectors:
            loc = page.locator(sel)
            if loc.count() > 0:
                return loc
        return None

    def _safe_get_text(self, parent: Locator, selectors: List[str]) -> Optional[str]:
        """Tries candidate selectors and returns first non-empty text."""
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

    def extract_single_card(self, card: Locator) -> Dict[str, Optional[str]]:
        """Parses an individual property card using hybrid DOM + Regex parsing."""
        # 1. Address
        address = self._safe_get_text(card, [
            '[data-test="property-card-addr"]',
            'address[data-test="property-card-addr"]',
            'address',
            'a[data-test="property-card-link"]',
            'a[class*="StyledPropertyCardDataArea-anchor"]',
        ])

        # 2. Direct Listing URL
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
                        item_url = urljoin(self.base_url, raw_href.strip())
                        break
            except Exception:
                continue

        # 3. Price via DOM
        price = self._safe_get_text(card, [
            '[data-test="property-card-price"]',
            'span[data-test="property-card-price"]',
            'span[class*="StyledPrice"]',
            'div[class*="StyledPropertyCardDataArea-anchor"] span',
            'span:has-text("$")',
        ])

        # 4. Beds & Baths via DOM
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

        # 5. Regex Fallback: Inspect Card Inner Text
        try:
            raw_text = card.inner_text()
        except Exception:
            raw_text = ""

        if raw_text:
            if not price:
                price_match = re.search(
                    r"(?:\$|€|£|R\$|C\$|A\$)\s*\d{1,3}(?:[,\.]\d{3})*(?:\s*\/\s*(?:mo|month))?",
                    raw_text,
                )
                if price_match:
                    price = price_match.group(0).strip()

            if not beds:
                beds_match = re.search(
                    r"(\d+(?:\.\d+)?|\bStudio\b)\s*(?:bds?|beds?|bedrooms?|dormitorio[s]?|quarto[s]?)",
                    raw_text,
                    re.IGNORECASE,
                )
                if beds_match:
                    beds = beds_match.group(0).strip()

            if not baths:
                baths_match = re.search(
                    r"(\d+(?:\.\d+)?)\s*(?:ba|baths?|bathrooms?|baño[s]?|banheiro[s]?)",
                    raw_text,
                    re.IGNORECASE,
                )
                if baths_match:
                    baths = baths_match.group(0).strip()

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
