# Scalable Real Estate Web Scraper (Zillow)

[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![Playwright](https://img.shields.io/badge/Playwright-Automated%20Browser-green.svg)](https://playwright.dev/python/)
[![Pandas](https://img.shields.io/badge/Pandas-Data%20Engineering-orange.svg)](https://pandas.pydata.org/)
[![Docker](https://img.shields.io/badge/Docker-Containerized-2496ED.svg)](https://www.docker.com/)

A production-grade, fault-tolerant web scraping and ETL data pipeline targeting real estate listings on **Zillow**. Built with an Object-Oriented architecture using **Python**, **Playwright (Sync API)** for JavaScript rendering and anti-bot mitigation, **Pandas** for schema cleaning, and **Docker** for cloud deployment.

---

## 📌 Project Architecture

```
Scalable-web-scraper/
├── src/
│   ├── __init__.py
│   ├── scraper.py          # Core OOP scraping engine with Playwright
│   └── pipeline.py         # Data cleaning, normalization, and CSV export
├── data/                   # Data output directory (CSV/JSON artifacts)
├── .env.example            # Environment configuration template
├── .gitignore              # Production-grade gitignore rules
├── Dockerfile              # Containerized headless environment
├── requirements.txt        # Pinned dependencies
└── README.md               # Project documentation
```

---

## 🚀 Key Features

* **Dynamic JavaScript Rendering**: Handles single-page app (SPA) hydration, infinite scrolls, and dynamic DOM updates using Playwright's headless browser.
* **Anti-Bot Mitigation**: Employs humanized user-agent strings, randomized navigation delays, and customized browser context headers to avoid basic bot triggers.
* **OOP Architecture**: Modular, maintainable, and extensible Python codebase following clean code principles.
* **Automated Data Cleaning Pipeline**: Parses raw scraped strings (prices, bed counts, bath counts, addresses) into normalized numeric and categorical formats using Pandas.
* **Production Deployment Ready**: Fully containerized using Docker to guarantee seamless execution across local machines, AWS EC2, or GCP Cloud Run.

---

## 🛠️ Tech Stack & Dependencies

* **Language**: Python 3.10+
* **Browser Automation**: [Playwright (Python Sync API)](https://playwright.dev/python/)
* **Data Processing**: [Pandas](https://pandas.pydata.org/) & [Pydantic](https://docs.pydantic.dev/)
* **Environment Configuration**: [python-dotenv](https://github.com/theskumar/python-dotenv)
* **Containerization**: Docker

---

## 💼 Custom Data Extraction Services

Looking for customized data scraping, API integrations, or large-scale web extraction pipelines?

* **E-commerce**: Price monitoring, competitor catalog scraping, inventory tracking.
* **Real Estate**: MLS, Zillow, Redfin data extraction with geolocation normalization.
* **Lead Generation**: B2B directories, job boards, business listings.

Feel free to connect or reach out for custom freelance data engineering projects!
