"""Scalable Dynamic Web Scraper package.

This file marks the 'src' directory as an importable Python package
and defines which modules are exposed to external scripts.
"""

# Import the high-level scraper orchestrator class
from src.scraper import DynamicWebScraper

# Import the browser lifecycle manager (launches & closes Chromium)
from src.browser import BrowserManager

# Import the anti-bot challenge resolver (handles Press & Hold CAPTCHAs)
from src.bot_handler import BotChallengeHandler

# Import the card data extractor (parses prices, beds, baths, addresses, URLs)
from src.extractor import ListingExtractor

# Import the infinite scroll and multi-page pagination engine
from src.scroller import InfiniteScroller

# Import the interactive GUI configuration dialogs
from src.config_gui import get_or_prompt_config, get_or_prompt_target_url

# Current semantic version of this package
__version__ = "0.3.0"

# Explicitly list public symbols exported when someone does 'from src import *'
__all__ = [
    "DynamicWebScraper",
    "BrowserManager",
    "BotChallengeHandler",
    "ListingExtractor",
    "InfiniteScroller",
    "get_or_prompt_config",
    "get_or_prompt_target_url",
]
