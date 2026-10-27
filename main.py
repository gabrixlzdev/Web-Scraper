"""Main execution entry point for the Dynamic Web Scraper.

Demonstrates launching the persistent browser, handling challenges,
scrolling to hydrate JavaScript elements, and live data extraction.
Keeps the browser open until the user chooses to close it.
"""

from src.scraper import DynamicWebScraper


def run_demo():
    """Runs a live demonstration of browser navigation and extraction."""
    print("==================================================")
    print("   Starting Dynamic Web Scraper (Playwright Sync)")
    print("==================================================")

    # Use the context manager ('with' block):
    # Initializes persistent context on entry, and cleans up when the block finishes
    with DynamicWebScraper() as scraper:
        print("[+] Browser launched successfully.")

        # Navigate to target search page and handle any bot challenge
        success = scraper.navigate()

        if success:
            print("[+] Page loaded successfully!")

            # Scroll down to hydrate lazy-loaded listing cards
            scraper.scroll_page(num_scrolls=2, delay=1.0)

            # Extract property data (price, address, beds, baths)
            listings = scraper.extract_listings(max_items=10)

            print("\n================ Extracted Listings ================")
            if listings:
                for idx, item in enumerate(listings, start=1):
                    print(
                        f"[{idx:02d}] "
                        f"Price: {item.get('price') or 'N/A':<12} | "
                        f"Beds: {item.get('beds') or 'N/A':<8} | "
                        f"Baths: {item.get('baths') or 'N/A':<8} | "
                        f"Addr: {item.get('address') or 'N/A'}"
                    )
            else:
                print("[!] No listings could be extracted from this page.")
            print("====================================================\n")

        else:
            print("[!] Failed to load target URL.")

        # Keep browser open indefinitely until user presses Enter in terminal:
        # This prevents the window from closing abruptly so you can inspect the page,
        # solve any challenges, or demonstrate the live site.
        input("\n[?] Browser is active and open. Press Enter in this terminal to close it...")

    print("[+] Scraper finished and browser closed cleanly.")


if __name__ == "__main__":
    run_demo()
