"""Scalable Dynamic Web Scraper package."""

from src.scraper import DynamicWebScraper
from src.config_gui import get_or_prompt_target_url

__version__ = "0.1.0"
__all__ = ["DynamicWebScraper", "get_or_prompt_target_url"]
