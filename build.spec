# build.spec

import sys
import os
from pathlib import Path
from PyInstaller.utils.hooks import collect_data_files

# --- Basic Setup ---
SRC_DIR = 'src'
# Determine project root relative to THIS spec file
project_root = os.path.dirname(os.path.abspath(__file__)) if '__file__' in locals() else os.path.abspath('.')
src_path = os.path.join(project_root, SRC_DIR)

# --- !!! ADD src TO SYS.PATH !!! ---
print(f"DEBUG [Spec]: Adding src path to sys.path: {src_path}")
sys.path.insert(0, src_path)
# --- !!! END ADD !!! ---

# --- Set DJANGO_SETTINGS_MODULE Environment Variable ---
# Ensure PyInstaller hooks know which settings to use
settings_module = 'quizpy_config.settings'
print(f"DEBUG [Spec]: Setting DJANGO_SETTINGS_MODULE to {settings_module}")
os.environ['DJANGO_SETTINGS_MODULE'] = settings_module
# --- END SET ---

# --- Application Entry Point ---
script_entry_point = os.path.join(SRC_DIR, 'run_waitress.py')

# --- Output Configuration ---
app_name = 'QuizPyRunner'
output_dir = 'dist'

# --- PyInstaller Analysis ---
# pathex might be less critical now sys.path is modified, but keep for analysis start point
pathex = [project_root]

# Binary files
binaries = []

# Non-code data files
datas = [
    ('static', 'static'),
    ('templates', 'templates'),
    ('data', 'data'),
    (os.path.join(SRC_DIR, 'db.sqlite3'), '.')
]

# Hidden imports (include settings module itself now?)
hiddenimports = [
    'django.contrib.admin', 'django.contrib.auth', 'django.contrib.contenttypes',
    'django.contrib.sessions', 'django.contrib.messages', 'django.contrib.staticfiles',
    'core', 'core.json_storage',
    'authentication', 'quiz', 'quiz.views',
    'student_interface', 'teacher_interface',
    'waitress',
    'openpyxl',
    'django.template.backends.django',
    'quizpy_config', # <<< Add settings package
    'quizpy_config.settings', # <<< Add settings module
    'quizpy_config.wsgi'
]

# Excludes
excludes = ['pytest', 'unittest', 'tests', '_pytest']

# --- Build Objects ---
print("DEBUG [Spec]: Starting Analysis...")
a = Analysis(
    [script_entry_point],
    pathex=pathex,
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=excludes,
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)
print("DEBUG [Spec]: Analysis Complete.")

# --- Define project_root using SPECPATH ---
project_root_spec = SPECPATH # Use SPECPATH available after Analysis
print(f"DEBUG: Project Root (SPECPATH) = {project_root_spec}")
icon_path = os.path.join(project_root_spec, 'static', 'favicon.ico')
print(f"DEBUG: Icon Path = {icon_path}")


pyz = PYZ(a.pure, a.zipped_data, cipher=None)
print("DEBUG [Spec]: PYZ created.")

exe = EXE( # ... arguments as before ...
    pyz, a.scripts, [], exclude_binaries=True, name=app_name, debug=False,
    bootloader_ignore_signals=False, strip=False, upx=False, console=True,
    disable_windowed_traceback=False, argv_emulation=False, target_arch=None,
    codesign_identity=None, entitlements_file=None, icon=None
)
print("DEBUG [Spec]: EXE object created.")

coll = COLLECT( # ... arguments as before ...
    exe, a.binaries, a.zipfiles, a.datas, strip=False, upx=False, name=app_name
)
print("DEBUG [Spec]: COLLECT object created.")