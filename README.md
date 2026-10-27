# Scalable Dynamic Web Scraper & ETL Pipeline

[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![Playwright](https://img.shields.io/badge/Playwright-Automated%20Browser-green.svg)](https://playwright.dev/python/)
[![Pandas](https://img.shields.io/badge/Pandas-Data%20Engineering-orange.svg)](https://pandas.pydata.org/)
[![Docker](https://img.shields.io/badge/Docker-Containerized-2496ED.svg)](https://www.docker.com/)

A production-grade, fault-tolerant web scraping and ETL data pipeline designed for modern JavaScript-heavy websites. Built with a decoupled Object-Oriented architecture using **Python**, **Playwright (Sync API)** for browser automation and anti-bot mitigation, **Pandas** for schema cleaning, and **Docker** for cloud deployment.

---

## 📌 Project Architecture

```
Scalable-web-scraper/
├── src/
│   ├── __init__.py          # Package initialization & exports
│   ├── browser.py           # Playwright lifecycle, persistent context & stealth flags
│   ├── bot_handler.py       # PerimeterX & CAPTCHA detection and Press-and-Hold solver
│   ├── extractor.py         # Hybrid DOM + Regex card extraction (price, address, beds, baths, url)
│   ├── scroller.py          # Infinite scroll engine with real-time deduplication
│   ├── scraper.py           # High-level orchestrator class (DynamicWebScraper)
│   ├── config_gui.py        # Native GUI modal for URL selection & .env persistence
│   └── pipeline.py          # Data cleaning, normalization, and CSV export
├── data/                    # Output directory (CSV/JSON artifacts)
├── .env.example             # Environment configuration template
├── .gitignore               # Production-grade gitignore rules
├── Dockerfile               # Containerized headless environment
├── main.py                  # Live demonstration runner
├── requirements.txt         # Pinned dependencies
└── README.md                # Project documentation
```

---

## 🚀 Quick Start Guide

Follow these steps to run the scraper locally on your machine:

### 1. Clone the repository & create a virtual environment
```bash
# Clone the repository
git clone https://github.com/<your-username>/Scalable-web-scraper.git
cd Scalable-web-scraper

# Create a virtual environment (isolates dependencies)
python -m venv venv

# Activate the virtual environment
# On Windows (PowerShell):
.\venv\Scripts\Activate.ps1
# On Windows (CMD):
.\venv\Scripts\activate.bat
# On Linux / macOS:
source venv/bin/activate
```

### 2. Install dependencies & Playwright browser binaries
```bash
# Install Python packages
python -m pip install -r requirements.txt

# Download the Chromium browser engine used by Playwright
python -m playwright install chromium
```

### 3. Run the scraper demonstration
```bash
python main.py
```

> **Interactive User Experience**:
> 1. **URL & Volume Selection Modal**: Native GUI dialog prompts you to confirm/enter the target URL and desired item count (or `0` for Unlimited Mode). Settings are automatically persisted to `.env`.
> 2. **Persistent Browser Session**: Chromium launches with session profile persistence (`browser_profile/`), saving cookies to bypass repetitive bot checks.
> 3. **Infinite Scroll & Multi-Page Traversal**: The engine scrolls each page container to hydrate lazy cards and automatically advances through the pagination bar (`[Next >]`) until your requested target count is fulfilled.
> 4. **Automated CSV Export**: Extracted listings are automatically cleaned with Pandas (prices converted to numeric integers, addresses split into city/state/zip) and saved to `data/listings_<timestamp>.csv`.
> 5. **Inspection Hold**: The browser window remains open until you press **Enter** in your terminal.

---

## 📊 Cleaned Data Schema (CSV Output)

Each run automatically exports a timestamped spreadsheet to the `data/` directory with the following clean schema:

| Column | Type | Example | Description |
| :--- | :--- | :--- | :--- |
| `price_clean` | Integer | `1149000` | Normalized numeric price (currency & symbols stripped) |
| `beds_clean` | Float | `4.0` | Bedroom count (`0.0` for Studio apartments) |
| `baths_clean` | Float | `3.0` | Bathroom count (e.g. `2.5`, `3.0`) |
| `street` | String | `9037 S Deer Creek Canyon Road` | Parsed street address |
| `city` | String | `Littleton` | Extracted city name |
| `state` | String | `CO` | Two-letter state code |
| `zip_code` | String | `80127` | 5-digit ZIP code |
| `url` | String | `https://www.zillow.com/homedetails/...` | Direct clickable link to the listing |
| `price_raw` | String | `$1,149,000` | Original unprocessed scraped price string |
| `address_raw` | String | `9037 S Deer Creek Canyon Road...` | Original unprocessed address string |
| `extracted_at` | DateTime | `2026-10-27 13:15:00` | ISO timestamp when the record was processed |

---

## ⚙️ Environment Variables Reference

Configure these settings inside your local `.env` file (or automatically via the GUI modal):

| Variable | Default Value | Description |
| :--- | :--- | :--- |
| `TARGET_URL` | `https://www.zillow.com/austin-tx/` | The target search/category URL to scrape |
| `MAX_ITEMS` | `50` | Desired listing extraction count (`0` = Unlimited Mode) |
| `HEADLESS` | `False` | `True` for silent cloud/Docker runs, `False` for visual demo |
| `SCRAPER_TIMEOUT` | `30000` | Maximum wait time in milliseconds for network requests |
| `USER_DATA_DIR` | `browser_profile` | Local directory storing cookies and persistent session state |

---

## 🛡️ Anti-Bot & Stealth Capabilities

* **Persistent Session Profiles**: Uses `launch_persistent_context` to retain authentic cookies, cache, and session tokens across runs in `browser_profile/`, avoiding fresh-bot detection flags.
* **Automation Flag Masking**: Automatically strips `navigator.webdriver` via `--disable-blink-features=AutomationControlled`.
* **Automated Press-and-Hold Solver**: Detects PerimeterX/DataDome verification overlays and simulates realistic human mouse down/hold/up interactions.
* **Targeted Container Scrolling**: Uses JavaScript execution to scroll `#search-page-list-container` directly, preventing map zooming.
* **Multi-Page Auto-Progression**: Automatically detects the end of the current page feed and advances through pagination buttons (`[Next >]`) or URL parameters.
* **Real-Time Deduplication**: Uses set-based memory hashing to prevent duplicate listings during infinite scrolling.

---

## 🛠️ Tech Stack

* **Language**: Python 3.10+
* **Browser Automation**: [Playwright (Python Sync API)](https://playwright.dev/python/)
* **GUI / Configuration**: [Tkinter](https://docs.python.org/3/library/tkinter.html) & [python-dotenv](https://github.com/theskumar/python-dotenv)
* **Data Processing**: [Pandas](https://pandas.pydata.org/) & [Pydantic](https://docs.pydantic.dev/)
* **Containerization**: Docker

---

## 💼 Custom Data Extraction & Engineering Services

Need reliable, high-volume data extraction or custom scrapers built for your business?

* **E-Commerce & Retail**: Price monitoring, product catalogs, stock tracking.
* **Real Estate & Listings**: Property metrics, addresses, pricing trends.
* **Lead Generation**: B2B directories, job boards, business contact data.
* **Custom ETL Pipelines**: Clean CSV, JSON, PostgreSQL, or Google Sheets exports.

Available for freelance orders and custom data engineering contracts.
