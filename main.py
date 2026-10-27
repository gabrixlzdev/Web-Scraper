"""Main execution entry point for the Dynamic Web Scraper.

Features:
- Native GUI dialog to confirm/enter target URL and desired item count (with .env persistence)
- Supports Unlimited Mode (0 = ALL available listings)
- Persistent anti-detection Chromium session (retaining cookies across runs)
- Automated handling of bot challenge overlays
- Infinite scroll pagination engine with real-time deduplication
- Resilient property data extraction (Price, Address, Beds, Baths, and Link URL)
- Interactive keep-alive until user chooses to close
"""

from src.scraper import DynamicWebScraper
from src.config_gui import get_or_prompt_config


def run_demo():
    """Runs an end-to-end extraction session with interactive URL and count selection."""
    print("==================================================")
    print("   Starting Dynamic Web Scraper (Playwright Sync)")
    print("==================================================")

    # 1. Prompt user via GUI popup for target URL and volume limit
    selected_url, max_items = get_or_prompt_config()
    limit_label = "UNLIMITED" if max_items <= 0 else str(max_items)
    print(f"[*] Target URL: {selected_url}")
    print(f"[*] Target Volume: {limit_label} listings")

    # 2. Use the context manager ('with' block):
    with DynamicWebScraper(target_url=selected_url) as scraper:
        print("[+] Browser launched successfully.")

        # Navigate to target page and handle any bot challenge
        success = scraper.navigate()

        if success:
            print("[+] Page loaded successfully!")

            # Run infinite scroll extraction for the requested count (dynamically scales scroll steps)
            listings = scraper.extract_listings(target_count=max_items)

            print(f"\n================ Extracted Listings ({len(listings)} Total) ================")
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
