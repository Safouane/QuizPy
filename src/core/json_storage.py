# src/core/json_storage.py
"""
Handles loading from and saving data to the quiz_data.json file.
Includes logic to determine the correct data path whether running
from source or as a packaged executable (e.g., PyInstaller).
"""

import json
import os
import sys
from pathlib import Path
import copy  # For returning copies safely

# --- Path Determination Logic ---


def get_base_dir() -> Path:
    """
    Determines the base directory of the application.
    If running as a frozen executable (PyInstaller), it assumes the base
    is the directory containing the executable.
    Otherwise (running from source), it assumes this script is located at
    'src/core/json_storage.py' and calculates the project root (QuizPy/)
    by going up three parent directories. Includes fallbacks.
    """
    print("DEBUG [json_storage GetBaseDir]: Determining base directory...")
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        # Running in a PyInstaller bundle (frozen)
        # sys.executable is the path to the executable
        base_dir = Path(sys.executable).parent.resolve()  # Use resolved absolute path
        print(
            f"DEBUG [json_storage GetBaseDir]: Detected packaged execution. Base dir (parent of executable): {base_dir}"
        )
    else:
        # Running as standard Python script
        try:
            # Assumes this file is at src/core/json_storage.py
            # Path(__file__) -> path to this file
            # .resolve()  -> absolute path
            # .parent      -> src/core/
            # .parent      -> src/
            # .parent      -> QuizPy/ (project root)
            base_dir = Path(__file__).resolve().parent.parent.parent
            print(
                f"DEBUG [json_storage GetBaseDir]: Running from source. Calculated base path (3 levels up from __file__): {base_dir}"
            )
            # Basic sanity check - does 'src' subdirectory exist?
            if not (base_dir / "src").is_dir():
                print(
                    f"WARNING [json_storage GetBaseDir]: Calculated source base path '{base_dir}' might be incorrect (missing 'src' subdir). Falling back."
                )
                raise RuntimeError("Path calculation likely incorrect")
        except Exception as e:
            print(
                f"ERROR [json_storage GetBaseDir]: Could not calculate source path reliably ({e}). Falling back to Current Working Directory."
            )
            # Fallback assumes script is run from the project root directory (QuizPy/)
            base_dir = Path.cwd().resolve()
            print(
                f"DEBUG [json_storage GetBaseDir]: Using fallback base dir (cwd): {base_dir}"
            )
    return base_dir


# --- Define Core Data and Media Directory Paths ---
try:
    BASE_DIR = get_base_dir()
    # Assume 'data' directory is directly under the base directory
    DATA_DIR = BASE_DIR / "data"
    # Define the main data file path
    DATA_FILE = DATA_DIR / "quiz_data.json"
    # Define the main media directory path
    MEDIA_DIR = DATA_DIR / "media"  # Used by get_media_dir helper

    # Ensure data directory exists (create if needed)
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    print(f"INFO [json_storage]: Data directory ensured at: {DATA_DIR}")
    print(f"INFO [json_storage]: Data file path set to: {DATA_FILE}")
    print(f"INFO [json_storage]: Media directory path set to: {MEDIA_DIR}")

except Exception as e:
    print(
        f"CRITICAL ERROR [json_storage]: Could not determine or create data directory paths: {e}"
    )
    # Set paths to None to indicate failure, functions below will handle this
    DATA_DIR = None
    DATA_FILE = None
    MEDIA_DIR = None


# --- Function to get media directory (used by views) ---
def get_media_dir() -> Path | None:
    """
    Returns the Path object for the media directory, ensuring it exists.
    Returns None if the base DATA_DIR path could not be determined.
    """
    if not MEDIA_DIR:
        print("ERROR [json_storage get_media_dir]: MEDIA_DIR path is not set.")
        return None
    try:
        # Ensure it exists (should already from module level, but check again)
        MEDIA_DIR.mkdir(parents=True, exist_ok=True)
        return MEDIA_DIR
    except Exception as e:
        print(
            f"ERROR [json_storage get_media_dir]: Could not create/access media directory {MEDIA_DIR}: {e}"
        )
        return None


# --- Function to load data ---
def load_data() -> dict:
    """
    Loads and parses data from the JSON file defined by DATA_FILE.
    Returns a default structure containing empty lists for quizzes,
    questions, and attempts if the file doesn't exist, is empty, or is invalid.
    """
    # Define the default structure to return on failure
    default_data = {"quizzes": [], "questions": [], "attempts": []}

    if not DATA_FILE:  # Check if path resolution failed earlier
        print(
            "ERROR [json_storage load_data]: DATA_FILE path not set. Returning default."
        )
        return copy.deepcopy(default_data)  # Return copy

    if not DATA_FILE.exists() or os.path.getsize(DATA_FILE) == 0:
        # Handle file not existing OR being empty
        print(
            f"WARNING [json_storage load_data]: File not found or empty at {DATA_FILE}. Returning default."
        )
        # Optionally, create an empty file here?
        # save_data(default_data) # Careful not to overwrite intended data if used incorrectly
        return copy.deepcopy(default_data)  # Return copy

    try:
        # Open with UTF-8 encoding for broader compatibility
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Validate that the loaded data is a dictionary
        if not isinstance(data, dict):
            print(
                f"ERROR [json_storage load_data]: Data in {DATA_FILE} is not a dictionary (type: {type(data)}). Returning default."
            )
            return copy.deepcopy(default_data)

        # Ensure top level keys exist, defaulting to empty lists if missing
        data.setdefault("quizzes", [])
        data.setdefault("questions", [])
        data.setdefault("attempts", [])

        # Optional: Further validation of list types within keys?
        if not isinstance(data["quizzes"], list):
            data["quizzes"] = []
        if not isinstance(data["questions"], list):
            data["questions"] = []
        if not isinstance(data["attempts"], list):
            data["attempts"] = []

        # print(f"INFO [json_storage load_data]: Successfully loaded data from {DATA_FILE}") # Can be verbose
        return data  # Return the loaded and potentially cleaned data

    except json.JSONDecodeError as e:
        print(
            f"ERROR [json_storage load_data]: Invalid JSON in {DATA_FILE}: {e}. Returning default."
        )
        return copy.deepcopy(default_data)  # Return copy
    except Exception as e:
        print(
            f"ERROR [json_storage load_data]: Failed to read {DATA_FILE}: {e}. Returning default."
        )
        import traceback

        traceback.print_exc()  # Log full traceback for unexpected errors
        return copy.deepcopy(default_data)  # Return copy


# --- Function to save data ---
def save_data(data: dict):
    """
    Saves the provided dictionary data to the JSON file defined by DATA_FILE.
    Uses UTF-8 encoding and pretty-printing (indent=2).
    Performs basic check to ensure data is a dictionary.
    """
    if not DATA_FILE:  # Check if path resolution failed
        print("ERROR [json_storage save_data]: DATA_FILE path not set. Cannot save.")
        # Optionally raise an exception here
        return

    if not isinstance(data, dict):
        print(
            f"ERROR [json_storage save_data]: Invalid data type provided for saving (expected dict, got {type(data)}). Aborting save."
        )
        return

    try:
        # Ensure parent directory exists before writing (belt-and-suspenders)
        DATA_FILE.parent.mkdir(parents=True, exist_ok=True)

        # Write with UTF-8 encoding and indentation
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        # print(f"INFO [json_storage save_data]: Successfully saved data to {DATA_FILE}") # Can be verbose

    except TypeError as e:
        # Often happens if data contains non-serializable types (like sets, datetime objects without custom serializer)
        print(
            f"ERROR [json_storage save_data]: Data not JSON serializable: {e}. Data type: {type(data)}"
        )
        # Consider logging details about the non-serializable object if possible without printing huge data
    except Exception as e:
        print(
            f"ERROR [json_storage save_data]: Failed to save data to {DATA_FILE}: {e}"
        )
        import traceback

        traceback.print_exc()  # Log full traceback
