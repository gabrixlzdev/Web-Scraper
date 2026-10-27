"""Module for interactive GUI-based target URL configuration and .env persistence.

EDUCATIONAL NOTE:
Tkinter is Python's standard built-in GUI library. It requires no external pip packages
and runs natively on Windows, macOS, and Linux desktop environments.
"""

import os
from pathlib import Path
from typing import Optional


def update_env_target_url(new_url: str, env_path: Path = Path(".env")) -> None:
    """Updates or creates TARGET_URL in the local .env file."""
    new_url = new_url.strip()
    if not new_url:
        return

    # If .env does not exist, check if .env.example exists to use as base, or create fresh
    lines = []
    if env_path.exists():
        with open(env_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
    elif Path(".env.example").exists():
        with open(".env.example", "r", encoding="utf-8") as f:
            lines = f.readlines()

    updated = False
    new_lines = []
    for line in lines:
        if line.strip().startswith("TARGET_URL="):
            new_lines.append(f"TARGET_URL={new_url}\n")
            updated = True
        else:
            new_lines.append(line)

    if not updated:
        new_lines.append(f"\nTARGET_URL={new_url}\n")

    with open(env_path, "w", encoding="utf-8") as f:
        f.writelines(new_lines)

    # Keep in-memory os.environ synchronized
    os.environ["TARGET_URL"] = new_url


def get_or_prompt_target_url(env_path: Path = Path(".env")) -> str:
    """Prompts the user via a native GUI dialog to confirm or enter a target URL.

    - If a TARGET_URL exists in .env: asks if the user wants to reuse it.
    - If No (or no URL exists): displays an input dialog to paste a new URL.
    - Gracefully falls back to terminal CLI input if running in a headless/Docker environment.
    """
    # 1. Read existing saved URL
    current_url = os.getenv("TARGET_URL", "").strip()

    # Try launching native Tkinter GUI dialog
    try:
        import tkinter as tk
        from tkinter import messagebox, simpledialog

        # Initialize hidden root Tk window (prevents blank background window from lingering)
        root = tk.Tk()
        root.withdraw()
        # Bring popup to the front of all open Windows
        root.attributes("-topmost", True)

        chosen_url: Optional[str] = None

        if current_url:
            # Ask user if they want to keep the current URL
            reuse = messagebox.askyesno(
                title="Target URL Configuration",
                message=(
                    f"Saved target URL found:\n\n{current_url}\n\n"
                    "Do you want to use this URL for this session?"
                ),
            )
            if reuse:
                chosen_url = current_url
            else:
                # Prompt user for new URL with current as default
                prompted = simpledialog.askstring(
                    title="Enter Target URL",
                    prompt="Enter the new website URL to scrape:",
                    initialvalue=current_url,
                )
                if prompted and prompted.strip():
                    chosen_url = prompted.strip()
                    update_env_target_url(chosen_url, env_path)
                else:
                    chosen_url = current_url
        else:
            # First time setup: prompt user directly
            prompted = simpledialog.askstring(
                title="Enter Target URL",
                prompt="Enter the target URL to scrape (e.g. https://www.zillow.com/austin-tx/):",
                initialvalue="https://www.zillow.com/austin-tx/",
            )
            chosen_url = (prompted or "https://www.zillow.com/austin-tx/").strip()
            update_env_target_url(chosen_url, env_path)

        root.destroy()
        return chosen_url or "https://www.zillow.com/austin-tx/"

    except Exception as e:
        # Fallback for headless environments (Docker, SSH, Linux servers without desktop)
        print(f"[*] GUI prompt unavailable ({e}). Using CLI fallback.")
        if current_url:
            return current_url
        return "https://www.zillow.com/austin-tx/"
