"""Main execution entry point for the Dynamic Web Scraper.

Features:
- Native GUI dialog to confirm or enter a target URL (with .env persistence)
- Persistent anti-detection Chromium session (retaining cookies across runs)
- Automated handling of bot challenge overlays
- Lazy-load DOM hydration via humanized scrolling
- Resilient property data extraction (Price, Address, Beds, Baths, and Link URL)
- Interactive keep-alive until user chooses to close
"""

from src.scraper import DynamicWebScraper
from src.config_gui import get_or_prompt_target_url


def run_demo():
    """Runs an end-to-end extraction session with interactive URL selection."""
    print("==================================================")
    print("   Starting Dynamic Web Scraper (Playwright Sync)")
    print("==================================================")

    # 1. Prompt user via GUI popup to confirm or update target URL
    selected_url = get_or_prompt_target_url()
    print(f"[*] Target URL selected: {selected_url}")

    # 2. Use the context manager ('with' block):
    # Initializes persistent context with chosen URL and cleans up when finished
    with DynamicWebScraper(target_url=selected_url) as scraper:
        print("[+] Browser launched successfully.")

        # Navigate to target page and handle any bot challenge
        success = scraper.navigate()

        if success:
            print("[+] Page loaded successfully!")

            # Scroll down to hydrate lazy-loaded listing cards
            scraper.scroll_page(num_scrolls=2, delay=1.0)

            # Extract property data (price, address, beds, baths, url)
            listings = scraper.extract_listings(max_items=10)

            print("\n================ Extracted Listings ================")
            if listings:
                for idx, item in enumerate(listings, start=1):
                    print(
                        f"[{idx:02d}] "
                        f"Price: {item.get('price') or 'N/A':<12} | "
                        f"Beds: {item.get('beds') or 'N/A':<8} | "
                        f"Baths: {item.get('baths') or 'N/A':<8}\n"
                        f"     Addr:  {item.get('address') or 'N/A'}\n"
                        f"     Link:  {item.get('url') or 'N/A'}\n"
                    )
            else:
                print("[!] No listings could be extracted from this page.")
            print("====================================================\n")

        else:
            print("[!] Failed to load target URL.")

        # Keep browser open indefinitely until user presses Enter in terminal
        input("\n[?] Browser is active and open. Press Enter in this terminal to close it...")

    print("[+] Scraper finished and browser closed cleanly.")


if __name__ == "__main__":
    run_demo()
