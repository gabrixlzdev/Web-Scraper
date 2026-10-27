"""Scalable Dynamic Web Scraper package."""

from src.scraper import DynamicWebScraper
from src.browser import BrowserManager
from src.bot_handler import BotChallengeHandler
from src.extractor import ListingExtractor
from src.scroller import InfiniteScroller
from src.config_gui import get_or_prompt_config, get_or_prompt_target_url

__version__ = "0.3.0"
__all__ = [
    "DynamicWebScraper",
    "BrowserManager",
    "BotChallengeHandler",
    "ListingExtractor",
    "InfiniteScroller",
    "get_or_prompt_config",
    "get_or_prompt_target_url",
]
