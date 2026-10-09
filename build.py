#!/usr/bin/env python3
"""Build script for creating standalone executables."""

import subprocess
import sys
from pathlib import Path


def build_exe():
    """Build Windows executable using PyInstaller."""
    print("Building Minecraft Mod Porter EXE...")

    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--onefile",
        "--windowed",
        "--name=ModPorter",
        "--icon=assets/icon.ico" if Path("assets/icon.ico").exists() else "",
        "--add-data=app:app",
        "run_app.py",
    ]

    cmd = [c for c in cmd if c]
    result = subprocess.run(cmd)

    if result.returncode == 0:
        print("\n✓ Build complete!")
        print(f"  EXE: dist/ModPorter.exe")
        print("  You can now distribute this file.")
    else:
        print("\n✗ Build failed.")
        sys.exit(1)


if __name__ == "__main__":
    build_exe()
