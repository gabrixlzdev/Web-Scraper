"""Data cleaning, transformation, and CSV export pipeline using Pandas."""

# Regular expressions for text pattern matching
import re
# Datetime for generating timestamps
from datetime import datetime
# Pathlib for cross-platform file paths (Windows '\' vs Linux '/')
from pathlib import Path
from typing import Dict, List, Optional
# Pandas: High-performance data manipulation library
import pandas as pd


class DataPipeline:
    """Cleans, normalizes, and exports scraped real estate records."""

    def __init__(self, raw_listings: List[Dict[str, Optional[str]]]) -> None:
        # Store the list of scraped dictionaries received from the scraper
        self.raw_listings = raw_listings
        # Holds the cleaned Pandas DataFrame (starts as None)
        self.df: Optional[pd.DataFrame] = None

    def clean_data(self) -> pd.DataFrame:
        """Transforms raw strings into structured, typed columns using Pandas."""
        # Handle empty results gracefully by returning an empty DataFrame with proper column names
        if not self.raw_listings:
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

        # 1. Convert Python list of dictionaries into a 2D tabular DataFrame
        df = pd.DataFrame(self.raw_listings)

        # 2. Preserve original raw values for audit and verification
        df["price_raw"] = df["price"]
        df["address_raw"] = df["address"]

        # --- 3. Clean Price Column ---
        # Remove '$', '€', commas, and text like '/mo' (keep only numeric digits)
        price_numeric = df["price"].astype(str).str.replace(r"[^\d]", "", regex=True)
        # Convert text digits into real numeric numbers (integers/floats)
        df["price_clean"] = pd.to_numeric(price_numeric, errors="coerce")

        # --- 4. Clean Bedrooms Column ---
        beds_raw = df["beds"].astype(str)
        # Identify rows that are Studio apartments
        is_studio = beds_raw.str.contains("Studio", case=False, na=False)
        # Extract the digits before 'bd' or 'bed' (e.g. "4 bds" -> "4")
        beds_extracted = beds_raw.str.extract(r"(\d+(?:\.\d+)?)")[0]
        # Convert string to float
        df["beds_clean"] = pd.to_numeric(beds_extracted, errors="coerce")
        # Set studio apartments to 0.0 bedrooms
        df.loc[is_studio, "beds_clean"] = 0.0

        # --- 5. Clean Bathrooms Column ---
        # Extract numeric digits (e.g. "2.5 baths" -> "2.5")
        baths_extracted = df["baths"].astype(str).str.extract(r"(\d+(?:\.\d+)?)")[0]
        # Convert to float
        df["baths_clean"] = pd.to_numeric(baths_extracted, errors="coerce")

        # --- 6. Parse Address into Street, City, State, and Zip ---
        # Regex pattern matching standard US addresses: 'Street, City, State Zip'
        address_pattern = (
            r"^(?P<street>.+?),\s*(?P<city>[^,]+?),\s*(?P<state>[A-Z]{2})\s*(?P<zip_code>\d{5})?$"
        )
        address_parts = df["address"].astype(str).str.extract(address_pattern)

        # Assign parsed parts into distinct columns
        df["street"] = address_parts["street"]
        df["city"] = address_parts["city"]
        df["state"] = address_parts["state"]
        df["zip_code"] = address_parts["zip_code"]

        # If an address format did not match the regex, preserve full address in the street column
        unmatched_mask = df["street"].isna() & df["address"].notna()
        df.loc[unmatched_mask, "street"] = df.loc[unmatched_mask, "address"]

        # --- 7. Add Extraction Timestamp ---
        # Records the exact date and time this batch was processed
        df["extracted_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Arrange columns in a logical spreadsheet order
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
        # Keep only existing columns to avoid KeyError
        existing_cols = [c for c in final_columns if c in df.columns]
        self.df = df[existing_cols]

        return self.df

    def export_csv(
        self,
        output_dir: str = "data",
        filename: Optional[str] = None,
    ) -> Path:
        """Cleans data and saves it to a timestamped CSV spreadsheet."""
        # Ensure data has been cleaned before saving
        if self.df is None:
            self.clean_data()

        # Create output directory on disk if it does not exist yet
        dest_dir = Path(output_dir)
        dest_dir.mkdir(parents=True, exist_ok=True)

        # Generate unique timestamped filename (e.g. listings_20261027_131500.csv)
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"listings_{timestamp}.csv"

        filepath = dest_dir / filename

        # Export DataFrame to CSV:
        # index=False: do not write Pandas 0, 1, 2 row numbers
        # encoding='utf-8-sig': includes UTF-8 BOM so Microsoft Excel on Windows opens it properly
        self.df.to_csv(filepath, index=False, encoding="utf-8-sig")
        print(f"[+] Cleaned dataset successfully exported to: {filepath.resolve()}")
        return filepath
