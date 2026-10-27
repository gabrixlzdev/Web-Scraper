"""Module for interactive GUI-based configuration and .env persistence.

Supports selecting target URLs and setting desired extraction volume
(with 0 / 'all' representing Unlimited Mode).
"""

import os
from pathlib import Path
from typing import Optional, Tuple


def update_env_variable(key: str, value: str, env_path: Path = Path(".env")) -> None:
    """Updates or inserts a key-value setting in the local .env file."""
    value = value.strip()
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
        if line.strip().startswith(f"{key}="):
            new_lines.append(f"{key}={value}\n")
            updated = True
        else:
            new_lines.append(line)

    if not updated:
        new_lines.append(f"\n{key}={value}\n")

    with open(env_path, "w", encoding="utf-8") as f:
        f.writelines(new_lines)

    os.environ[key] = value


def get_or_prompt_config(env_path: Path = Path(".env")) -> Tuple[str, int]:
    """Prompts the user via native GUI dialogs for target URL and desired item count.

    Returns:
        Tuple of (target_url, max_items). max_items=0 denotes Unlimited Mode.
    """
    current_url = os.getenv("TARGET_URL", "").strip()
    saved_items_str = os.getenv("MAX_ITEMS", "50").strip()

    try:
        import tkinter as tk
        from tkinter import messagebox, simpledialog

        root = tk.Tk()
        root.withdraw()
        root.attributes("-topmost", True)

        chosen_url: str = ""

        # --- 1. Target URL Prompt ---
        if current_url:
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
                prompted = simpledialog.askstring(
                    title="Enter Target URL",
                    prompt="Enter the new website URL to scrape:",
                    initialvalue=current_url,
                )
                if prompted and prompted.strip():
                    chosen_url = prompted.strip()
                    update_env_variable("TARGET_URL", chosen_url, env_path)
                else:
                    chosen_url = current_url
        else:
            prompted = simpledialog.askstring(
                title="Enter Target URL",
                prompt="Enter the target URL to scrape (e.g. https://www.zillow.com/austin-tx/):",
                initialvalue="https://www.zillow.com/austin-tx/",
            )
            chosen_url = (prompted or "https://www.zillow.com/austin-tx/").strip()
            update_env_variable("TARGET_URL", chosen_url, env_path)

        # --- 2. Extraction Count Prompt (Unlimited or Specific Number) ---
        count_prompt = simpledialog.askstring(
            title="Extraction Volume",
            prompt=(
                "How many listings do you want to extract?\n\n"
                "• Enter a number (e.g. 50, 100, 250)\n"
                "• Enter 0 for UNLIMITED (scrapes until end of feed)"
            ),
            initialvalue=saved_items_str or "50",
        )

        try:
            max_items = int(count_prompt.strip()) if count_prompt else 50
        except ValueError:
            max_items = 0 if count_prompt and "all" in count_prompt.lower() else 50

        update_env_variable("MAX_ITEMS", str(max_items), env_path)

        root.destroy()
        return chosen_url, max_items

    except Exception as e:
        print(f"[*] GUI prompt unavailable ({e}). Using CLI/environment defaults.")
        default_url = current_url or "https://www.zillow.com/austin-tx/"
        default_items = int(saved_items_str) if saved_items_str.isdigit() else 50
        return default_url, default_items


# Backwards compatibility alias
get_or_prompt_target_url = lambda: get_or_prompt_config()[0]
