"""
Setup script untuk Irma Virtual Assistant
Install dependencies dan download required models
"""

import subprocess
import sys
import os
from pathlib import Path
import urllib.request
import zipfile
import shutil

def print_step(message):
    """Print step dengan format"""
    print(f"\n{'='*60}")
    print(f"  {message}")
    print(f"{'='*60}\n")

def run_command(command, description):
    """Run command dengan error handling"""
    print(f"Running: {description}")
    try:
        result = subprocess.run(command, shell=True, check=True, 
                              capture_output=True, text=True)
        print(f"Success: {description}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error: {description}")
        print(f"  {e.stderr}")
        return False

def download_vosk_model():
    """Download Vosk model untuk Bahasa Indonesia"""
    print_step("Downloading Vosk Model")
    
    models_dir = Path("models")
    models_dir.mkdir(exist_ok=True)
    
    model_name = "vosk-model-small-id-0.22"
    model_path = models_dir / model_name
    
    if model_path.exists():
        print(f"Model already exists: {model_path}")
        return True
    
    # Download URL
    model_url = f"https://alphacephei.com/vosk/models/{model_name}.zip"
    zip_path = models_dir / f"{model_name}.zip"
    
    print(f"Downloading from: {model_url}")
    print("This may take a few minutes...")
    
    try:
        # Download
        urllib.request.urlretrieve(model_url, zip_path)
        print(f"Downloaded to: {zip_path}")
        
        # Extract
        print("Extracting model...")
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(models_dir)
        
        # Remove zip
        zip_path.unlink()
        
        print(f"Model extracted to: {model_path}")
        return True
        
    except Exception as e:
        print(f"Failed to download model: {e}")
        print("\nAlternative: Download manually from:")
        print(model_url)
        print(f"Extract to: {models_dir.absolute()}")
        return False

def create_venv():
    """Create virtual environment"""
    print_step("Creating Virtual Environment")
    
    venv_path = Path("venv")
    
    if venv_path.exists():
        print("Virtual environment already exists")
        return True
    
    return run_command(
        f"{sys.executable} -m venv venv",
        "Creating venv"
    )

def install_requirements():
    """Install Python requirements"""
    print_step("Installing Python Dependencies")
    
    # Determine pip path
    if sys.platform == "win32":
        pip = "venv\\Scripts\\pip.exe"
        python = "venv\\Scripts\\python.exe"
    else:
        pip = "venv/bin/pip"
        python = "venv/bin/python"
    
    # Upgrade pip
    run_command(
        f"{python} -m pip install --upgrade pip",
        "Upgrading pip"
    )
    
    # Install requirements
    return run_command(
        f"{pip} install -r requirements.txt",
        "Installing requirements"
    )

def check_tesseract():
    """Check Tesseract OCR installation"""
    print_step("Checking Tesseract OCR")
    
    try:
        result = subprocess.run(
            ["tesseract", "--version"],
            capture_output=True,
            text=True
        )
        print("Tesseract is installed")
        print(result.stdout.split('\n')[0])
        return True
    except FileNotFoundError:
        print("WARNING: Tesseract OCR is NOT installed")
        print("\nTesseract required for screen reading feature.")
        print("Download from: https://github.com/UB-Mannheim/tesseract/wiki")
        print("After installation, add to PATH")
        return False

def check_pyaudio():
    """Check PyAudio installation"""
    print_step("Checking PyAudio")
    
    try:
        import pyaudio
        print("PyAudio is installed")
        return True
    except ImportError:
        print("WARNING: PyAudio is NOT installed")
        print("\nPyAudio required for microphone access.")
        print("Install with: pip install pipwin && pipwin install pyaudio")
        print("Or download wheel from: https://www.lfd.uci.edu/~gohlke/pythonlibs/#pyaudio")
        return False

def create_startup_script():
    """Create startup script"""
    print_step("Creating Startup Scripts")
    
    # Windows batch script
    batch_content = """@echo off
cd /d "%~dp0"
call venv\\Scripts\\activate.bat
python src\\main.py
pause
"""
    
    with open("run_irma.bat", "w") as f:
        f.write(batch_content)
    
    print("Created: run_irma.bat")
    
    # Python launcher
    launcher_content = """import subprocess
import sys
from pathlib import Path

venv_python = Path("venv/Scripts/python.exe")
if not venv_python.exists():
    venv_python = Path("venv/bin/python")

subprocess.run([str(venv_python), "src/main.py"])
"""
    
    with open("run_irma.py", "w") as f:
        f.write(launcher_content)
    
    print("Created: run_irma.py")
    
    return True

def main():
    """Main setup function"""
    print("\n")
    print("*" * 60)
    print("*" + " " * 58 + "*")
    print("*" + "  IRMA VIRTUAL ASSISTANT - SETUP  ".center(58) + "*")
    print("*" + " " * 58 + "*")
    print("*" * 60)
    
    # Change to project directory
    os.chdir(Path(__file__).parent)
    
    # Setup steps
    steps = [
        (create_venv, "Virtual Environment"),
        (install_requirements, "Dependencies"),
        (download_vosk_model, "Vosk Model"),
        (check_tesseract, "Tesseract OCR"),
        (check_pyaudio, "PyAudio"),
        (create_startup_script, "Startup Scripts"),
    ]
    
    results = []
    for func, name in steps:
        success = func()
        results.append((name, success))
    
    # Summary
    print_step("Setup Summary")
    
    for name, success in results:
        status = "OK" if success else "FAIL/WARNING"
        print(f"  {name:<30} [{status}]")
    
    print("\n")
    
    # Final instructions
    if all(success for _, success in results):
        print("Setup complete! All components ready.")
    else:
        print("Setup completed with warnings.")
        print("Check messages above for any missing components.")
    
    print("\nTo start Irma:")
    print("  1. Windows: Double-click 'run_irma.bat'")
    print("  2. Or run: python src/main.py")
    print("\nFirst-time setup may take a moment to initialize models.")
    print("\n")

if __name__ == "__main__":
    main()
