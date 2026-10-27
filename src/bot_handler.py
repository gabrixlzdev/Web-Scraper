"""Module responsible for detecting and mitigating anti-bot challenges.

EDUCATIONAL NOTE:
PerimeterX and DataDome challenge overlays frequently change their DOM selectors.
Keeping anti-bot mitigation in a dedicated module allows you to tweak evasion tactics
without touching core scraper navigation or data parsing code.
"""

import time
from typing import Optional
from playwright.sync_api import Page, Locator


class BotChallengeHandler:
    """Detects and handles anti-bot verification screens (e.g. PerimeterX Press & Hold)."""

    def __init__(self, page: Page) -> None:
        self.page = page

    def resolve_challenge(self, wait_seconds: int = 15) -> bool:
        """Inspects the page for challenge overlays and attempts automated resolution."""
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

        # Attempt automated press-and-hold mouse simulation
        if target_element:
            try:
                box = target_element.bounding_box()
                if box:
                    center_x = box["x"] + (box["width"] / 2)
                    center_y = box["y"] + (box["height"] / 2)
                    print("[*] Simulating human mouse Press-and-Hold for 6 seconds...")
                    self.page.mouse.move(center_x, center_y)
                    self.page.mouse.down()
                    time.sleep(6)
                    self.page.mouse.up()
                    time.sleep(2)
            except Exception as e:
                print(f"[!] Automated hold simulation failed: {e}")

        # Wait for challenge clearance
        print(f"[*] Waiting up to {wait_seconds}s for challenge clearance...")
        start_time = time.time()
        while time.time() - start_time < wait_seconds:
            if self.page.locator('article[data-test="property-card"], .photo-cards').count() > 0:
                print("[+] Bot challenge cleared! Listings rendered.")
                return True
            time.sleep(1.5)

        return False
