import subprocess
import sys
from pathlib import Path

venv_python = Path("venv/Scripts/python.exe")
if not venv_python.exists():
    venv_python = Path("venv/bin/python")

subprocess.run([str(venv_python), "src/main.py"])
