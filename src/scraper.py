"""Module containing the core DynamicWebScraper class skeleton.

EDUCATIONAL NOTE:
In professional data engineering and commercial freelancing (e.g. Fiverr),
scrapers are designed to be general-purpose and configurable rather than
hardcoded to a single trademarked brand. This allows you to reuse the same
engine across many client projects with minimal changes.
"""

import os
from typing import Dict, List, Optional
from pathlib import Path

# python-dotenv:
# Reads key-value pairs from a `.env` file and adds them to environment variables (os.environ).
from dotenv import load_dotenv

# Initialize environment variables from .env
load_dotenv()


class DynamicWebScraper:
    """Production-grade scraper for extracting data from dynamic websites.

    This class encapsulates browser automation settings, anti-detection
    configurations, and extracted data management.
    """

    def __init__(
        self,
        target_url: Optional[str] = None,
        headless: Optional[bool] = None,
        timeout: Optional[int] = None,
        user_agent: Optional[str] = None,
        output_dir: str = "data",
    ) -> None:
        """Initializes the DynamicWebScraper instance.

        Settings fallback hierarchy:
        1. Explicit argument passed into DynamicWebScraper(...)
        2. Environment variable from .env (e.g. os.getenv("HEADLESS"))
        3. Hardcoded safe default fallback value

        Args:
            target_url: The target website entry point.
            headless:
                - `True`: Browser runs silently in background (fast, server/Docker friendly).
                - `False`: Visual browser window pops up (client demo & debugging).
            timeout: Maximum wait time in milliseconds before timing out.
            user_agent: Browser header string mimicking human navigation.
            output_dir: Local directory where extracted CSV/JSON files will be stored.
        """
        # Resolve configurations: argument -> env var -> hardcoded default
        self.target_url = target_url or os.getenv("TARGET_URL", "https://www.zillow.com")

        if headless is not None:
            self.headless = headless
        else:
            # os.getenv returns a string, so we check if it equals "true" (case-insensitive)
            env_headless = os.getenv("HEADLESS", "False").strip().lower()
            self.headless = env_headless in ("true", "1", "yes")

        if timeout is not None:
            self.timeout = timeout
        else:
            self.timeout = int(os.getenv("SCRAPER_TIMEOUT", "30000"))

        # Modern Chrome User-Agent on Windows 10/11 to avoid immediate bot detection
        self.user_agent = (
            user_agent
            or os.getenv("USER_AGENT")
            or "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        )

        # Pathlib automatically handles path slashes regardless of OS (Windows '\' vs Linux '/')
        self.output_dir = Path(output_dir)
        # Create output directory if it doesn't already exist (mkdir -p equivalent)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # In-memory storage list where raw scraped records will accumulate
        self.raw_listings: List[Dict[str, Optional[str]]] = []


# Alias for backwards compatibility if referenced under a real estate alias
RealEstateScraper = DynamicWebScraper
