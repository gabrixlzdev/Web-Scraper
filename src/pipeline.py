"""Data cleaning, transformation, and CSV export pipeline using Pandas."""

import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
import pandas as pd


class DataPipeline:
    """Cleans, normalizes, and exports scraped real estate records."""

    def __init__(self, raw_listings: List[Dict[str, Optional[str]]]) -> None:
        # In-memory list of dictionaries extracted by the scraper
        self.raw_listings = raw_listings
        # Cleaned Pandas DataFrame (initialized as None until clean_data() runs)
        self.df: Optional[pd.DataFrame] = None

    def clean_data(self) -> pd.DataFrame:
        """Transforms raw strings into structured, typed columns using Pandas vectorized operations."""
        if not self.raw_listings:
            # Return an empty DataFrame with standard columns if no data was collected
            self.df = pd.DataFrame(
                columns=[
                    "price_clean",
                    "beds_clean",
                    "baths_clean",
                    "street",
                    "city",
                    "state",
                    "zip_code",
                    "price_raw",
                    "address_raw",
                    "url",
                    "extracted_at",
                ]
            )
            return self.df

        # 1. Convert list of dictionaries into a Pandas 2D DataFrame
        df = pd.DataFrame(self.raw_listings)

        # Preserve original raw strings for audit trail
        df["price_raw"] = df["price"]
        df["address_raw"] = df["address"]

        # --- 2. Clean Price Column ---
        # Remove currency symbols ($, €, £), commas, and text like '/mo'
        # e.g. "$1,149,000" -> "1149000"
        price_numeric = df["price"].astype(str).str.replace(r"[^\d]", "", regex=True)
        # pd.to_numeric converts strings to integers/floats; errors='coerce' turns invalid entries into NaN
        df["price_clean"] = pd.to_numeric(price_numeric, errors="coerce")

        # --- 3. Clean Bedrooms Column ---
        # Extract numeric digits or treat 'Studio' as 0 bedrooms
        beds_raw = df["beds"].astype(str)
        # Check if row is a Studio apartment
        is_studio = beds_raw.str.contains("Studio", case=False, na=False)
        # Extract numeric digits (e.g. "4 bds" -> "4")
        beds_extracted = beds_raw.str.extract(r"(\d+(?:\.\d+)?)")[0]
        df["beds_clean"] = pd.to_numeric(beds_extracted, errors="coerce")
        df.loc[is_studio, "beds_clean"] = 0.0

        # --- 4. Clean Bathrooms Column ---
        # Extract numeric bathroom count (e.g. "2.5 baths" -> "2.5")
        baths_extracted = df["baths"].astype(str).str.extract(r"(\d+(?:\.\d+)?)")[0]
        df["baths_clean"] = pd.to_numeric(baths_extracted, errors="coerce")

        # --- 5. Parse Address into Street, City, State, and Zip ---
        # Uses regex named capture groups to split standard US addresses:
        # e.g. "9037 S Deer Creek Canyon Road, Littleton, CO 80127"
        address_pattern = (
            r"^(?P<street>.+?),\s*(?P<city>[^,]+?),\s*(?P<state>[A-Z]{2})\s*(?P<zip_code>\d{5})?$"
        )
        address_parts = df["address"].astype(str).str.extract(address_pattern)

        # Merge extracted address columns into main DataFrame
        df["street"] = address_parts["street"]
        df["city"] = address_parts["city"]
        df["state"] = address_parts["state"]
        df["zip_code"] = address_parts["zip_code"]

        # Fallback for addresses that don't match the standard comma format
        unmatched_mask = df["street"].isna() & df["address"].notna()
        df.loc[unmatched_mask, "street"] = df.loc[unmatched_mask, "address"]

        # --- 6. Add Metadata Timestamp ---
        # ISO timestamp recording when this batch was processed
        df["extracted_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Reorder columns into a clean, professional spreadsheet layout
        final_columns = [
            "price_clean",
            "beds_clean",
            "baths_clean",
            "street",
            "city",
            "state",
            "zip_code",
            "url",
            "price_raw",
            "address_raw",
            "extracted_at",
        ]
        # Only include columns that exist in DataFrame
        existing_cols = [c for c in final_columns if c in df.columns]
        self.df = df[existing_cols]

        return self.df

    def export_csv(
        self,
        output_dir: str = "data",
        filename: Optional[str] = None,
    ) -> Path:
        """Cleans data and saves it to a timestamped CSV spreadsheet."""
        if self.df is None:
            self.clean_data()

        # Ensure destination data folder exists on disk
        dest_dir = Path(output_dir)
        dest_dir.mkdir(parents=True, exist_ok=True)

        # Generate unique timestamped filename if none provided
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"listings_{timestamp}.csv"

        filepath = dest_dir / filename

        # Export to CSV:
        # index=False: Excludes Pandas internal 0, 1, 2 row numbers
        # encoding='utf-8-sig': UTF-8 with Byte Order Mark, required for Excel on Windows to display cleanly
        self.df.to_csv(filepath, index=False, encoding="utf-8-sig")
        print(f"[+] Cleaned dataset successfully exported to: {filepath.resolve()}")
        return filepath
