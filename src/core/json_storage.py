# src/core/json_storage.py
import json
import os
import sys
from pathlib import Path
import copy  # Often useful for returning copies


# --- Define function to determine data file path ---
def get_data_file_path() -> Path:
    """
    Gets the correct path to quiz_data.json whether running from source or packaged.
    Handles potential execution contexts (script, frozen executable).
    Returns a Path object.
    """
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        # Running in a PyInstaller bundle
        # Assume 'data' dir is copied next to executable by PyInstaller spec.
        # This strategy requires the spec file to copy the 'data' folder
        # using the 'datas' argument: datas=[('data', 'data')]
        executable_dir = Path(sys.executable).parent
        data_dir = executable_dir / "data"
        print(
            f"DEBUG [json_storage GetPath]: Running packaged. Using path relative to exe: {data_dir}"
        )
    else:
        # Running as standard Python script
        # Assume this file is at src/core/json_storage.py
        # Go up three levels from here to reach the project root (QuizPy/)
        try:
            # Path(__file__) is the path to this json_storage.py file
            # .resolve() makes it absolute
            # .parent gets the 'core' directory
            # .parent.parent gets the 'src' directory
            # .parent.parent.parent gets the 'QuizPy' project root directory
            base_path = Path(__file__).resolve().parent.parent.parent
            data_dir = base_path / "data"
            print(
                f"DEBUG [json_storage GetPath]: Running from source. Calculated base path: {base_path}, data dir: {data_dir}"
            )
            if not base_path.exists() or not (base_path / "src").exists():
                print(
                    "WARNING [json_storage GetPath]: Calculated base path seems incorrect. Falling back."
                )
                raise RuntimeError("Path calculation failed")  # Force fallback
        except Exception as e:
            print(
                f"ERROR [json_storage GetPath]: Could not calculate standard path: {e}. Falling back to relative path."
            )
            # Fallback assumes script is run from project root (less reliable)
            data_dir = Path(".") / "data"

    # Ensure data directory exists (create if needed)
    try:
        data_dir.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        print(
            f"ERROR [json_storage GetPath]: Could not create data directory {data_dir}: {e}"
        )
        # Depending on requirements, could raise error or default to in-memory?

    # Return the full path to the JSON file
    return data_dir / "quiz_data.json"


# --- End function definition ---


# --- Define the path to the data file as a module-level constant ---
DATA_FILE = get_data_file_path()
print(f"INFO [json_storage]: Data file path set to: {DATA_FILE}")


# --- Function to load data ---
def load_data() -> dict:
    """
    Loads and parses data from the JSON file defined by DATA_FILE.
    Returns a default structure if the file doesn't exist or is invalid.
    """
    # Define the default structure to return on failure
    default_data = {"quizzes": [], "questions": [], "attempts": []}

    if not DATA_FILE:  # Check if path resolution failed earlier
        print(
            "ERROR [json_storage load_data]: DATA_FILE path not set. Returning default."
        )
        return copy.deepcopy(default_data)  # Return copy

    if not DATA_FILE.exists():
        print(
            f"WARNING [json_storage load_data]: File not found at {DATA_FILE}. Returning default."
        )
        return copy.deepcopy(default_data)  # Return copy

    try:
        # Open with UTF-8 encoding for broader compatibility
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        # Optional: Add validation here to ensure top-level keys exist?
        if not isinstance(data, dict):
            print(
                f"ERROR [json_storage load_data]: Data in {DATA_FILE} is not a dictionary. Returning default."
            )
            return copy.deepcopy(default_data)

        # Ensure top level keys exist
        data.setdefault("quizzes", [])
        data.setdefault("questions", [])
        data.setdefault("attempts", [])

        # print(f"INFO [json_storage load_data]: Successfully loaded data from {DATA_FILE}") # Can be noisy
        return data  # Return the loaded data
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
    """
    if not DATA_FILE:  # Check if path resolution failed
        print("ERROR [json_storage save_data]: DATA_FILE path not set. Cannot save.")
        return  # Or raise error

    try:
        # Ensure parent directory exists before writing (get_data_file_path should have done this)
        DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
        # Write with UTF-8 encoding and indentation
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        # print(f"INFO [json_storage save_data]: Successfully saved data to {DATA_FILE}") # Can be noisy
    except TypeError as e:
        # Often happens if data contains non-serializable types (like sets, datetime objects without serializer)
        print(
            f"ERROR [json_storage save_data]: Data not JSON serializable: {e}. Data was: {type(data)}"
        )  # Avoid printing large data
        # Add more detailed logging about *what* is not serializable if possible
    except Exception as e:
        print(
            f"ERROR [json_storage save_data]: Failed to save data to {DATA_FILE}: {e}"
        )
        import traceback

        traceback.print_exc()  # Log full traceback for unexpected errors
