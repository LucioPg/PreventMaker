import os
import sys
import subprocess
import shutil
from pathlib import Path

def build_executable():
    """
    Build the executable using PyInstaller
    """
    print("Building PreventMaker executable...")
    
    # Ensure PyInstaller is installed
    try:
        import PyInstaller
    except ImportError:
        print("PyInstaller not found. Installing...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
    
    # Create a temporary spec file
    spec_content = """
# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['preventmaker.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
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
    debug=False,
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
    icon='NONE',
)
    """
    
    with open("preventmaker.spec", "w") as f:
        f.write(spec_content)
    
    # Build the executable
    print("Running PyInstaller...")
    subprocess.check_call([
        sys.executable, 
        "-m", 
        "PyInstaller", 
        "preventmaker.spec",
        "--clean",
        "--noconfirm"
    ])
    
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