"""Module containing the core ZillowScraper class skeleton.

EDUCATIONAL NOTE:
In modern Python development, we organize scrapers into classes (Object-Oriented Programming).
This keeps configurations (timeouts, URLs, browser settings) bundled together with the
methods that execute the actions (launching browser, navigating, extracting data).
"""

import os
from typing import Dict, List, Optional
from pathlib import Path

# python-dotenv:
# Reads key-value pairs from a `.env` file and adds them to environment variables (os.environ).
from dotenv import load_dotenv

# Execute load_dotenv() when this module is imported.
# It looks for a `.env` file in the current working directory or parent directories.
load_dotenv()


class ZillowScraper:
    """Production-grade scraper for extracting property listings from Zillow.

    This class encapsulates browser configuration and data management.
    """

    def __init__(
        self,
        base_url: Optional[str] = None,
        headless: Optional[bool] = None,
        timeout: Optional[int] = None,
        user_agent: Optional[str] = None,
        output_dir: str = "data",
    ) -> None:
        """Initializes the ZillowScraper instance.

        Settings fallback hierarchy:
        1. Explicit argument passed into ZillowScraper(...)
        2. Environment variable from .env (e.g. os.getenv("HEADLESS"))
        3. Hardcoded safe default fallback value

        Args:
            base_url: The target website entry point.
            headless:
                - `True`: Browser runs silently in background (fast, server/Docker friendly).
                - `False`: Browser window physically opens (ideal for visual debugging).
            timeout: Maximum wait time in milliseconds before timing out.
            user_agent: Browser header string mimicking human navigation.
            output_dir: Local folder where extracted CSV/JSON files will be saved.
        """
        # Resolve configurations: argument -> env var -> hardcoded default
        self.base_url = base_url or os.getenv("BASE_URL", "https://www.zillow.com")

        if headless is not None:
            self.headless = headless
        else:
            # os.getenv returns a string, so we check if it equals "true" (case-insensitive)
            env_headless = os.getenv("HEADLESS", "True").strip().lower()
            self.headless = env_headless in ("true", "1", "yes")

        if timeout is not None:
            self.timeout = timeout
        else:
            self.timeout = int(os.getenv("SCRAPER_TIMEOUT", "30000"))

        # Fallback to a standard modern Chrome user agent if none was provided
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

        # In-memory storage list where raw scraped listing dictionaries will accumulate
        self.raw_listings: List[Dict[str, Optional[str]]] = []
