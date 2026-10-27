"""Anti-bot mitigation and CAPTCHA detection module."""

import time
from typing import Optional
from playwright.sync_api import Page, Locator


class BotChallengeHandler:
    """Detects and resolves anti-bot verification screens (e.g. PerimeterX Press & Hold)."""

    def __init__(self, page: Page) -> None:
        # Active Playwright browser tab
        self.page = page

    def resolve_challenge(self, wait_seconds: int = 15) -> bool:
        """Checks for challenge elements and simulates human mouse press-and-hold."""
        # CSS selectors for common verification frames and buttons
        challenge_selectors = [
            '#px-captcha',
            'div[id*="captcha"]',
            'button:has-text("Press & Hold")',
            'div:has-text("Press & Hold")',
            'iframe[title*="challenge"]',
        ]

        found_challenge = False
        target_element: Optional[Locator] = None

        # Look for any visible challenge elements on the page
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

        # If no challenge was detected, the page is clear
        if not found_challenge:
            return True

        # Simulate human mouse hold (move to center, mouse down, sleep 6s, mouse up)
        if target_element:
            try:
                box = target_element.bounding_box()
                if box:
                    center_x = box["x"] + (box["width"] / 2)
                    center_y = box["y"] + (box["height"] / 2)
                    print("[*] Simulating human mouse Press-and-Hold for 6 seconds...")
                    self.page.mouse.move(center_x, center_y)  # Move cursor to button
                    self.page.mouse.down()                   # Press left mouse button
                    time.sleep(6)                            # Hold down for 6 seconds
                    self.page.mouse.up()                     # Release left mouse button
                    time.sleep(2)
            except Exception as e:
                print(f"[!] Automated hold simulation failed: {e}")

        # Wait up to wait_seconds for the challenge to clear and cards to appear
        print(f"[*] Waiting up to {wait_seconds}s for challenge clearance...")
        start_time = time.time()
        while time.time() - start_time < wait_seconds:
            # Check if property cards are now visible
            if self.page.locator('article[data-test="property-card"], .photo-cards').count() > 0:
                print("[+] Bot challenge cleared! Listings rendered.")
                return True
            time.sleep(1.5)

        return False
