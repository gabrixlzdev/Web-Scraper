"""Main execution entry point for the Dynamic Web Scraper."""

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

    # 2. Use context manager ('with' block): launches browser and ensures clean exit
    with DynamicWebScraper(target_url=selected_url) as scraper:
        print("[+] Browser launched successfully.")

        # Navigate to target search page and handle any bot challenge
        success = scraper.navigate()

        if success:
            print("[+] Page loaded successfully!")

            # Extract listings using infinite scroll and multi-page pagination
            listings = scraper.extract_listings(target_count=max_items)

            # Display extracted results in formatted console table
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

        # Keep browser open until user presses Enter in terminal for inspection
        input("\n[?] Browser is active and open. Press Enter in this terminal to close it...")

    print("[+] Scraper finished and browser closed cleanly.")


if __name__ == "__main__":
    run_demo()
