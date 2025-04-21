# src/run_waitress.py
import os
import sys

# NOTE: DO NOT import webbrowser or threading here yet (that's for step 4)
print("INFO: Starting run_waitress.py...")

# --- Determine if running packaged ---
# This helps adjust paths if needed, though get_base_dir should handle it
IS_FROZEN = getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS")
print(f"INFO: Running as packaged executable? {IS_FROZEN}")
if IS_FROZEN:
    # When frozen, code might be extracted to a temp dir (_MEIPASS)
    # Or it might run directly from the installation dir (sys.executable parent)
    # Our get_base_dir() in json_storage handles this detection.
    print(f"INFO: Executable Dir: {os.path.dirname(sys.executable)}")
    if hasattr(sys, "_MEIPASS"):
        print(f"INFO: MEIPASS Temp Dir: {sys._MEIPASS}")
    # Add bundled directories to path if necessary (PyInstaller usually does this)
    # basedir = os.path.dirname(__file__) # This might not work correctly when frozen
    # sys.path.insert(0, os.path.abspath(".")) # Add current dir where exe might be?
    # sys.path.insert(0, os.path.join(sys._MEIPASS)) # Add temp dir? Needed?

# --- Configure Django Settings ---
# PyInstaller hook should generally handle setting this environment variable
# based on the spec file, but setting it defensively doesn't hurt.
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "quizpy_config.settings")
print(
    f"INFO: DJANGO_SETTINGS_MODULE set to: {os.environ.get('DJANGO_SETTINGS_MODULE')}"
)

# --- Import Django/Waitress AFTER potential path adjustments ---
try:
    from waitress import serve

    # Important: Import the WSGI app *after* setting DJANGO_SETTINGS_MODULE
    from quizpy_config.wsgi import application

    print("INFO: Django WSGI application imported successfully.")
except ImportError as e:
    print(f"ERROR: Failed to import Django/Waitress or WSGI application: {e}")
    print("ERROR: Ensure Django is installed and DJANGO_SETTINGS_MODULE is correct.")
    input("Press Enter to exit...")  # Keep console open
    sys.exit(1)
except Exception as e:
    print(f"ERROR: An unexpected error occurred during imports: {e}")
    input("Press Enter to exit...")
    sys.exit(1)


# --- Server Configuration ---
HOST = "127.0.0.1"  # Listen only on localhost
PORT = 8000  # Standard port, ensure it's free
# Waitress default threads = 4, adjust if needed waitress.serve(..., threads=8)

# --- Run Server ---
if __name__ == "__main__":
    print("------------------------------------------")
    print("      Starting QuizPy Server via Waitress      ")
    print("------------------------------------------")
    print(f"INFO: Server Address: http://{HOST}:{PORT}")
    print(f"INFO: Django Settings: {os.environ.get('DJANGO_SETTINGS_MODULE')}")
    print("INFO: Press Ctrl+C in this window to stop the server.")
    print("------------------------------------------")
    try:
        serve(application, host=HOST, port=PORT)
    except Exception as e:
        print(f"ERROR: Failed to start Waitress server: {e}")
        input("Press Enter to exit...")
        sys.exit(1)
