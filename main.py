"""Main execution entry point for the Dynamic Web Scraper.

Demonstrates launching the browser, anti-detection context initialization,
and live navigation.
"""

import time
from src.scraper import DynamicWebScraper


def run_demo():
    """Runs a live demonstration of browser initialization and navigation."""
    print("==================================================")
    print("   Starting Dynamic Web Scraper (Playwright Sync)")
    print("==================================================")

    # Use the context manager ('with' block):
    # This automatically calls scraper.start_browser() upon entering,
    # and scraper.close_browser() upon exiting (even if an error occurs).
    with DynamicWebScraper() as scraper:
        print("[+] Browser launched successfully.")
        
        # Navigate to the configured target URL
        success = scraper.navigate()

        if success:
            print("[+] Page loaded successfully!")
            print("[*] Pausing 5 seconds so you can see the active page...")
            time.sleep(5)
        else:
            print("[!] Failed to load target URL.")

    print("[+] Scraper finished and browser closed cleanly.")


if __name__ == "__main__":
    run_demo()
