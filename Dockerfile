# ==============================================================================
# Production Dockerfile for Dynamic Web Scraper
# ==============================================================================

# Use Microsoft's official Playwright Python image based on Ubuntu Jammy.
# This image comes with all Linux OS libraries, C++ runtimes, and Chromium pre-installed.
FROM mcr.microsoft.com/playwright/python:v1.40.0-jammy

# Set working directory inside the container
WORKDIR /app

# PYTHONUNBUFFERED=1 ensures console logs (print statements) stream immediately without buffering
# HEADLESS=True forces Chromium to run without an X11 display inside Docker
ENV PYTHONUNBUFFERED=1 \
    HEADLESS=True \
    DEBIAN_FRONTEND=noninteractive

# Copy dependencies list first (Docker caches this layer if requirements haven't changed)
COPY requirements.txt .

# Install Python packages without caching installation archives (keeps image small)
RUN pip install --no-cache-dir -r requirements.txt

# Ensure Playwright browser binaries are linked and up to date
RUN playwright install chromium

# Copy application source code and entry points into the container
COPY src/ ./src/
COPY main.py .
COPY .env.example .

# Create data and browser profile directories inside the container
RUN mkdir -p /app/data /app/browser_profile

# Default command executed when container starts
CMD ["python", "main.py"]
