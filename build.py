import os
import sys
import subprocess
from pathlib import Path
from pyinstaller_utils import resource_path

def build_executable():
    """
    Build the executable using PyInstaller for Windows 11
    """
    print("Building PreventMaker executable for Windows 11...")

    # Ensure PyInstaller is installed
    try:
        import PyInstaller
    except ImportError:
        print("PyInstaller not found. Installing...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])

    # Define icon path
    icon_path = resource_path("icons/PreventMaker.ico").replace("\\", "/")
    icons_folder = os.path.join(os.getcwd(), 'icons')
    resources_list = []

    # Aggiungi tutte le icone dalla cartella 'icons'
    if os.path.exists(icons_folder):
        for file in os.listdir(icons_folder):
            file_path = os.path.join(icons_folder, file)
            if os.path.isfile(file_path) and file.endswith(('.ico', '.png', '.jpg', '.svg')):
                # Formato (percorso_origine, percorso_destinazione)
                resources_list.append((file_path, 'icons'))
    datas_str = str(resources_list).replace("'", "\"")
    # Create a temporary spec file
    spec_content = f"""
# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['preventmaker.py'],
    pathex=[],
    binaries=[],
    datas={datas_str},
    hiddenimports=[
        'PyQt6.QtWebEngineWidgets', 
        'PyQt6.QtWebEngineCore', 
        'reportlab', 
        'PyPDF2',
        'dotenv',
        'python-dotenv',
        'custom_events',
        'products_enums',
        'qcode',
        'utils',
        'constants',
        'json',
        'tempfile',

    ],
    hookspath=[],
    hooksconfig={{}},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='PreventMaker',
    debug=True,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='{icon_path}',
    uac_admin=False,
)
    """

    with open("preventmaker.spec", "w") as f:
        f.write(spec_content)

    # Build the executable
    print("Running PyInstaller for Windows 11...")

    # Set environment variable to ensure Windows 11 compatibility
    os.environ['PYTHONIOENCODING'] = 'utf-8'

    # Build command for Windows 11
    build_cmd = [
        sys.executable, 
        "-m", 
        "PyInstaller",
        "preventmaker.spec",
        "--clean",
        "--noconfirm"
        # Note: --windowed and --uac-admin options are now defined in the spec file
    ]

    try:
        subprocess.check_call(build_cmd)
    except subprocess.CalledProcessError as e:
        print(f"Error during build: {e}")
        return None

    # Check if build was successful
    dist_dir = Path("dist")
    exe_path = dist_dir / "PreventMaker.exe"

    if exe_path.exists():
        print(f"Build successful! Executable created at: {exe_path.absolute()}")
        return str(exe_path.absolute())
    else:
        print("Build failed. Executable not found.")
        return None

if __name__ == "__main__":
    build_executable()
