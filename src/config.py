import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Base Paths
BASE_DIR = Path(__file__).parent.parent
SRC_DIR = BASE_DIR / "src"
MODELS_DIR = BASE_DIR / "models"
LOGS_DIR = BASE_DIR / "logs"
CONFIG_DIR = BASE_DIR / "config"
DATABASE_DIR = BASE_DIR / "database"
TRAINING_DIR = DATABASE_DIR / "training"

# Ensure directories exist
LOGS_DIR.mkdir(exist_ok=True)
MODELS_DIR.mkdir(exist_ok=True)
CONFIG_DIR.mkdir(exist_ok=True)
DATABASE_DIR.mkdir(exist_ok=True)
TRAINING_DIR.mkdir(exist_ok=True)

# App Settings
APP_NAME = os.getenv("APP_NAME", "Irma")
VERSION = os.getenv("VERSION", "1.0.0")

# Voice Settings
VOICE_GENDER = os.getenv("VOICE_GENDER", "female")
VOICE_RATE = int(os.getenv("VOICE_RATE", 175))
VOICE_VOLUME = float(os.getenv("VOICE_VOLUME", 1.0))

# Wake Word
WAKE_WORD = os.getenv("WAKE_WORD", "hey irma")
WAKE_WORD_SENSITIVITY = float(os.getenv("WAKE_WORD_SENSITIVITY", 0.5))

# Memory Management
MAX_MEMORY_PERCENT = int(os.getenv("MAX_MEMORY_PERCENT", 80))
GC_THRESHOLD = int(os.getenv("GC_THRESHOLD", 50))
AUTO_CLEANUP_ENABLED = os.getenv("AUTO_CLEANUP_ENABLED", "true").lower() == "true"

# Security Settings
ZERO_TRUST_MODE = os.getenv("ZERO_TRUST_MODE", "true").lower() == "true"
AUDIT_LOG_ENABLED = os.getenv("AUDIT_LOG_ENABLED", "true").lower() == "true"
MAX_FILE_SIZE_MB = int(os.getenv("MAX_FILE_SIZE_MB", 100))

# Whitelist Directories
USER_HOME = Path.home()
WHITELIST_DIRS_STR = os.getenv("WHITELIST_DIRS", "Downloads,Documents\\Irma")
WHITELIST_DIRS = [USER_HOME / dir_name.strip() for dir_name in WHITELIST_DIRS_STR.split(",")]

# Add database directory to whitelist (untuk internal use)
WHITELIST_DIRS.append(DATABASE_DIR)
WHITELIST_DIRS.append(TRAINING_DIR)

# Critical System Paths to BLOCK
BLOCKED_PATHS = [
    Path("C:\\Windows"),
    Path("C:\\Program Files"),
    Path("C:\\Program Files (x86)"),
    Path("C:\\ProgramData"),
    USER_HOME / "AppData",
    Path("C:\\System Volume Information"),
]

# Internet Settings
WEB_REQUEST_TIMEOUT = int(os.getenv("WEB_REQUEST_TIMEOUT", 5))
MAX_REQUESTS_PER_MINUTE = int(os.getenv("MAX_REQUESTS_PER_MINUTE", 10))
ALLOWED_DOMAINS_STR = os.getenv("ALLOWED_DOMAINS", "wikipedia.org,google.com")
ALLOWED_DOMAINS = [domain.strip() for domain in ALLOWED_DOMAINS_STR.split(",")]

# Screen Reading
OCR_LANGUAGE = os.getenv("OCR_LANGUAGE", "ind+eng")
SCREEN_CAPTURE_DELAY = int(os.getenv("SCREEN_CAPTURE_DELAY", 1))

# Listening Settings
ENERGY_THRESHOLD = int(os.getenv("ENERGY_THRESHOLD", 300))
PAUSE_THRESHOLD = float(os.getenv("PAUSE_THRESHOLD", 0.8))
PHRASE_TIME_LIMIT = int(os.getenv("PHRASE_TIME_LIMIT", 10))
AMBIENT_DURATION = int(os.getenv("AMBIENT_DURATION", 1))

# Vosk Model Path
VOSK_MODEL_PATH = MODELS_DIR / "vosk-model-small-id-0.22"

# Audit Log Path
AUDIT_LOG_PATH = LOGS_DIR / "security_audit.log"
ERROR_LOG_PATH = LOGS_DIR / "errors.log"
