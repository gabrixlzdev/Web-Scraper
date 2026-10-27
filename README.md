# Scalable Dynamic Web Scraper & ETL Pipeline

[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![Playwright](https://img.shields.io/badge/Playwright-Automated%20Browser-green.svg)](https://playwright.dev/python/)
[![Pandas](https://img.shields.io/badge/Pandas-Data%20Engineering-orange.svg)](https://pandas.pydata.org/)
[![Docker](https://img.shields.io/badge/Docker-Containerized-2496ED.svg)](https://www.docker.com/)

A production-grade, fault-tolerant web scraping and ETL data pipeline designed for modern JavaScript-heavy websites. Built with an Object-Oriented architecture using **Python**, **Playwright (Sync API)** for browser automation and anti-bot mitigation, **Pandas** for schema cleaning, and **Docker** for cloud deployment.

---

## 📌 Project Architecture

```
Scalable-web-scraper/
├── src/
│   ├── __init__.py
│   ├── scraper.py          # Core OOP browser automation engine
│   └── pipeline.py         # Data cleaning, normalization, and CSV export
├── data/                   # Output directory (CSV/JSON artifacts)
├── .env.example            # Environment configuration template
├── .gitignore              # Production-grade gitignore rules
├── Dockerfile              # Containerized headless environment
├── main.py                 # Live demonstration runner
├── requirements.txt        # Pinned dependencies
└── README.md               # Project documentation
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

### 3. Configure environment settings
```bash
# Copy example configuration template to create your .env
# On Windows:
copy .env.example .env
# On Linux / macOS:
cp .env.example .env
```
*(By default, `HEADLESS=False` in `.env` so you can visually watch the browser window pop up and run).*

### 4. Run the scraper demonstration
```bash
python main.py
```

---

## ⚙️ Key Features

* **Dynamic JavaScript Rendering**: Handles single-page applications (SPAs), infinite scroll, and delayed DOM hydration via Playwright's browser engine.
* **Anti-Bot & Stealth Browsing**: Employs humanized User-Agents, configurable viewport dimensions, and automated navigation delays to bypass basic automated bot detection.
* **Modular OOP Architecture**: Decoupled engine allowing easy adaptation to diverse e-commerce, real estate, or directory target platforms.
* **Automated Data Cleaning Pipeline**: Cleans, parses, and typecasts raw extracted text (prices, numeric metrics, addresses) into clean tabular datasets using Pandas.
* **Production Deployment Ready**: Containerized via Docker to run seamlessly on local environments or cloud instances (AWS EC2, GCP, DigitalOcean).

---

## 🛠️ Tech Stack

* **Language**: Python 3.10+
* **Browser Automation**: [Playwright (Python Sync API)](https://playwright.dev/python/)
* **Data Processing**: [Pandas](https://pandas.pydata.org/) & [Pydantic](https://docs.pydantic.dev/)
* **Configuration**: [python-dotenv](https://github.com/theskumar/python-dotenv)
* **Containerization**: Docker

---

## 💼 Custom Data Extraction Services (Fiverr Portfolio)

Need reliable, high-volume data extraction or custom scrapers built for your business?

* **E-Commerce & Retail**: Price monitoring, product catalogs, stock tracking.
* **Real Estate & Listings**: Property metrics, addresses, pricing trends.
* **Lead Generation**: B2B directories, job boards, business contact data.
* **Custom ETL Pipelines**: Clean CSV, JSON, PostgreSQL, or Google Sheets exports.

Available for freelance orders and custom data engineering contracts.
