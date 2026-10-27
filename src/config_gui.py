"""Module for interactive GUI-based configuration and .env persistence.

Supports selecting target URLs and setting desired extraction volume
(with 0 / 'all' representing Unlimited Mode).
"""

# Standard Python modules for operating system and file path operations
import os
from pathlib import Path
from typing import Optional, Tuple


def update_env_variable(key: str, value: str, env_path: Path = Path(".env")) -> None:
    """Updates or inserts a key-value setting in the local .env file."""
    # Clean whitespace from the input value
    value = value.strip()
    lines = []

    # Read existing lines from .env if it already exists
    if env_path.exists():
        with open(env_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
    # Otherwise fallback to template .env.example if available
    elif Path(".env.example").exists():
        with open(".env.example", "r", encoding="utf-8") as f:
            lines = f.readlines()

    updated = False
    new_lines = []

    # Check each line: if the setting already exists, replace it with the new value
    for line in lines:
        if line.strip().startswith(f"{key}="):
            new_lines.append(f"{key}={value}\n")
            updated = True
        else:
            new_lines.append(line)

    # If the setting was not found in the file, append it at the bottom
    if not updated:
        new_lines.append(f"\n{key}={value}\n")

    # Write the updated lines back to the .env file on disk
    with open(env_path, "w", encoding="utf-8") as f:
        f.writelines(new_lines)

    # Synchronize the in-memory environment variable for the current Python session
    os.environ[key] = value


def get_or_prompt_config(env_path: Path = Path(".env")) -> Tuple[str, int]:
    """Prompts the user via native GUI dialogs for target URL and desired item count.

    Returns:
        Tuple of (target_url, max_items). max_items=0 denotes Unlimited Mode.
    """
    # Read currently saved settings from environment variables if present
    current_url = os.getenv("TARGET_URL", "").strip()
    saved_items_str = os.getenv("MAX_ITEMS", "50").strip()

    try:
        # Import Python's built-in GUI library (Tkinter)
        import tkinter as tk
        from tkinter import messagebox, simpledialog

        # Create a hidden background Tk window so only popup dialogs appear on screen
        root = tk.Tk()
        root.withdraw()

        # Force the popup window to stay in front of all open applications on Windows
        root.attributes("-topmost", True)

        chosen_url: str = ""

        # --- 1. Target URL Prompt ---
        # If a URL was previously saved in .env, ask if the user wants to reuse it
        if current_url:
            reuse = messagebox.askyesno(
                title="Target URL Configuration",
                message=(
                    f"Saved target URL found:\n\n{current_url}\n\n"
                    "Do you want to use this URL for this session?"
                ),
            )
            # If user clicked Yes: reuse the existing URL
            if reuse:
                chosen_url = current_url
            # If user clicked No: open text dialog to paste a new URL
            else:
                prompted = simpledialog.askstring(
                    title="Enter Target URL",
                    prompt="Enter the new website URL to scrape:",
                    initialvalue=current_url,
                )
                if prompted and prompted.strip():
                    chosen_url = prompted.strip()
                    # Save the new URL to .env for next time
                    update_env_variable("TARGET_URL", chosen_url, env_path)
                else:
                    chosen_url = current_url
        # If running for the first time with no saved URL, prompt directly
        else:
            prompted = simpledialog.askstring(
                title="Enter Target URL",
                prompt="Enter the target URL to scrape (e.g. https://www.zillow.com/austin-tx/):",
                initialvalue="https://www.zillow.com/austin-tx/",
            )
            chosen_url = (prompted or "https://www.zillow.com/austin-tx/").strip()
            # Save the entered URL to .env
            update_env_variable("TARGET_URL", chosen_url, env_path)

        # --- 2. Extraction Volume Prompt (Specific Number or 0 for Unlimited) ---
        count_prompt = simpledialog.askstring(
            title="Extraction Volume",
            prompt=(
                "How many listings do you want to extract?\n\n"
                "• Enter a number (e.g. 50, 100, 250)\n"
                "• Enter 0 for UNLIMITED (scrapes until end of feed)"
            ),
            initialvalue=saved_items_str or "50",
        )

        # Safely convert the input string to an integer
        try:
            max_items = int(count_prompt.strip()) if count_prompt else 50
        except ValueError:
            # If user typed 'all' or an invalid text, treat as 0 (unlimited) or fallback to 50
            max_items = 0 if count_prompt and "all" in count_prompt.lower() else 50

        # Save preferred count to .env
        update_env_variable("MAX_ITEMS", str(max_items), env_path)

        # Close the hidden GUI window
        root.destroy()
        return chosen_url, max_items

    except Exception as e:
        # Fallback for systems without a graphical display (e.g. Docker, cloud servers)
        print(f"[*] GUI prompt unavailable ({e}). Using CLI/environment defaults.")
        default_url = current_url or "https://www.zillow.com/austin-tx/"
        default_items = int(saved_items_str) if saved_items_str.isdigit() else 50
        return default_url, default_items


# Shorthand alias to get just the URL if needed
get_or_prompt_target_url = lambda: get_or_prompt_config()[0]
