"""
Setup Validator for Irma
Validates all dependencies and configurations before running
"""

import sys
import os
import subprocess
import json
from pathlib import Path


class Colors:
    """ANSI color codes"""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'


def print_header(text):
    """Print section header"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{text:^60}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.RESET}\n")


def print_success(text):
    """Print success message"""
    print(f"{Colors.GREEN}[OK]{Colors.RESET} {text}")


def print_error(text):
    """Print error message"""
    print(f"{Colors.RED}[ERROR]{Colors.RESET} {text}")


def print_warning(text):
    """Print warning message"""
    print(f"{Colors.YELLOW}[WARNING]{Colors.RESET} {text}")


def print_info(text):
    """Print info message"""
    print(f"{Colors.BLUE}[INFO]{Colors.RESET} {text}")


def check_python_version():
    """Check Python version"""
    print_info("Checking Python version...")
    version = sys.version_info
    
    if version.major == 3 and version.minor >= 8:
        print_success(f"Python {version.major}.{version.minor}.{version.micro}")
        return True
    else:
        print_error(f"Python {version.major}.{version.minor}.{version.micro} - Requires Python 3.8+")
        return False


def check_virtual_environment():
    """Check if running in virtual environment"""
    print_info("Checking virtual environment...")
    
    if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        print_success("Running in virtual environment")
        return True
    else:
        print_warning("Not running in virtual environment")
        print_info("Recommended: Run inside venv for isolation")
        return True  # Not critical, just warning


def check_package_installed(package_name, import_name=None):
    """Check if Python package is installed"""
    if import_name is None:
        import_name = package_name
    
    try:
        __import__(import_name)
        return True
    except ImportError:
        return False


def check_required_packages():
    """Check all required Python packages"""
    print_info("Checking required Python packages...")
    
    required = {
        'flask': 'flask',
        'flask-cors': 'flask_cors',
        'vosk': 'vosk',
        'pyttsx3': 'pyttsx3',
        'requests': 'requests',
        'beautifulsoup4': 'bs4',
        'pillow': 'PIL',
        'pytesseract': 'pytesseract',
        'opencv-python': 'cv2',
        'numpy': 'numpy',
        'psutil': 'psutil',
        'python-dotenv': 'dotenv',
    }
    
    missing = []
    for package, import_name in required.items():
        if check_package_installed(package, import_name):
            print_success(f"{package}")
        else:
            print_error(f"{package} - Not installed")
            missing.append(package)
    
    if missing:
        print_error(f"\nMissing packages: {', '.join(missing)}")
        print_info("Install with: pip install " + " ".join(missing))
        return False
    
    return True


def check_tesseract():
    """Check Tesseract OCR installation"""
    print_info("Checking Tesseract OCR...")
    
    try:
        result = subprocess.run(['tesseract', '--version'], 
                              capture_output=True, 
                              text=True, 
                              timeout=5)
        if result.returncode == 0:
            version = result.stdout.split('\n')[0]
            print_success(f"Tesseract OCR: {version}")
            return True
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass
    
    print_warning("Tesseract OCR not found in PATH")
    print_info("Optional: Install for screen reading feature")
    print_info("Download: https://github.com/UB-Mannheim/tesseract/wiki")
    return True  # Not critical


def check_vosk_model():
    """Check Vosk model availability"""
    print_info("Checking Vosk model...")
    
    model_path = Path("models/vosk-model-small-id-0.22")
    
    if model_path.exists() and model_path.is_dir():
        required_files = ['am', 'conf', 'graph', 'ivector']
        missing = [f for f in required_files if not (model_path / f).exists()]
        
        if not missing:
            print_success(f"Vosk model found: {model_path}")
            return True
        else:
            print_warning(f"Vosk model incomplete: missing {missing}")
    else:
        print_warning("Vosk model not found")
    
    print_info("Optional: Download for voice recognition")
    print_info("URL: https://alphacephei.com/vosk/models")
    return True  # Not critical for web interface


def check_env_file():
    """Check .env configuration file"""
    print_info("Checking .env configuration...")
    
    env_path = Path(".env")
    
    if not env_path.exists():
        print_error(".env file not found")
        print_info("Create .env file with required configuration")
        return False
    
    # Check required variables
    required_vars = ['WHITELIST_DIRS', 'ALLOWED_DOMAINS']
    
    try:
        with open(env_path, 'r') as f:
            content = f.read()
            
        missing = [var for var in required_vars if var not in content]
        
        if missing:
            print_warning(f"Missing variables in .env: {', '.join(missing)}")
        else:
            print_success(".env file configured")
        
        return True
        
    except Exception as e:
        print_error(f"Error reading .env: {e}")
        return False


def check_directory_structure():
    """Check required directory structure"""
    print_info("Checking directory structure...")
    
    required_dirs = [
        'src',
        'src/audio',
        'src/nlu',
        'src/security',
        'src/executors',
        'src/utils',
        'web',
        'web/templates',
        'models',
        'logs',
        'database',
        'database/training',
    ]
    
    all_exist = True
    for dir_path in required_dirs:
        path = Path(dir_path)
        if path.exists():
            print_success(f"{dir_path}/")
        else:
            print_error(f"{dir_path}/ - Missing")
            all_exist = False
    
    if not all_exist:
        print_info("Run setup.py to create missing directories")
    
    return all_exist


def check_web_interface():
    """Check web interface files"""
    print_info("Checking web interface files...")
    
    required_files = [
        'web/app.py',
        'web/templates/index.html',
    ]
    
    all_exist = True
    for file_path in required_files:
        path = Path(file_path)
        if path.exists():
            print_success(f"{file_path}")
        else:
            print_error(f"{file_path} - Missing")
            all_exist = False
    
    return all_exist


def check_port_available(port=5000):
    """Check if port is available"""
    print_info(f"Checking port {port} availability...")
    
    import socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    result = sock.connect_ex(('localhost', port))
    sock.close()
    
    if result != 0:
        print_success(f"Port {port} is available")
        return True
    else:
        print_error(f"Port {port} is already in use")
        print_info("Stop any running server or use different port")
        return False


def generate_validation_report(results):
    """Generate validation report"""
    print_header("VALIDATION REPORT")
    
    total = len(results)
    passed = sum(1 for r in results.values() if r)
    failed = total - passed
    
    print(f"Total Checks: {total}")
    print(f"{Colors.GREEN}Passed: {passed}{Colors.RESET}")
    print(f"{Colors.RED}Failed: {failed}{Colors.RESET}")
    
    if failed == 0:
        print(f"\n{Colors.GREEN}{Colors.BOLD}All checks passed! Ready to run Irma.{Colors.RESET}")
        return True
    else:
        print(f"\n{Colors.YELLOW}{Colors.BOLD}Some checks failed. Please fix issues above.{Colors.RESET}")
        
        # Check if critical failures
        critical = ['python_version', 'required_packages', 'directory_structure']
        critical_failed = any(not results[k] for k in critical if k in results)
        
        if critical_failed:
            print(f"{Colors.RED}Critical issues found. Cannot proceed.{Colors.RESET}")
            return False
        else:
            print(f"{Colors.YELLOW}Only optional features missing. Can proceed with limited functionality.{Colors.RESET}")
            return True


def main():
    """Main validation function"""
    print_header("IRMA SETUP VALIDATOR")
    print("Validating system configuration and dependencies...\n")
    
    results = {}
    
    # Run all checks
    print_header("SYSTEM CHECKS")
    results['python_version'] = check_python_version()
    results['virtual_environment'] = check_virtual_environment()
    
    print_header("DEPENDENCIES")
    results['required_packages'] = check_required_packages()
    results['tesseract'] = check_tesseract()
    results['vosk_model'] = check_vosk_model()
    
    print_header("CONFIGURATION")
    results['env_file'] = check_env_file()
    results['directory_structure'] = check_directory_structure()
    
    print_header("WEB INTERFACE")
    results['web_interface'] = check_web_interface()
    results['port_available'] = check_port_available()
    
    # Generate report
    success = generate_validation_report(results)
    
    if success:
        print(f"\n{Colors.BLUE}Next step: Run 'run_web.bat' to start Irma!{Colors.RESET}")
        return 0
    else:
        print(f"\n{Colors.RED}Fix the issues above before running Irma.{Colors.RESET}")
        return 1


if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print(f"\n\n{Colors.YELLOW}Validation cancelled.{Colors.RESET}")
        sys.exit(1)
    except Exception as e:
        print(f"\n{Colors.RED}Unexpected error: {e}{Colors.RESET}")
        sys.exit(1)
