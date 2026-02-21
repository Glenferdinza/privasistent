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
OCR_LANGUAGE = os.getenv("OCR_LANGUAGE", "eng+ind+msa+rus")
SCREEN_CAPTURE_DELAY = int(os.getenv("SCREEN_CAPTURE_DELAY", 1))

# Listening Settings
ENERGY_THRESHOLD = int(os.getenv("ENERGY_THRESHOLD", 300))
PAUSE_THRESHOLD = float(os.getenv("PAUSE_THRESHOLD", 0.8))
PHRASE_TIME_LIMIT = int(os.getenv("PHRASE_TIME_LIMIT", 10))
AMBIENT_DURATION = int(os.getenv("AMBIENT_DURATION", 1))

# Multi-Language Voice Settings
# === VOSK ENGINE ===
# NOTE: Indonesian & Malay models tidak tersedia di Vosk
# English model dapat recognize Indonesian text dengan akurasi ~60-70%
DEFAULT_VOICE_LANGUAGE = os.getenv("DEFAULT_VOICE_LANGUAGE", "en")  # en/ru (only available)
AVAILABLE_LANGUAGES = ['en', 'ru']  # English (universal), Russian

# Vosk Model Paths (ONLY models that actually exist)
VOSK_MODELS = {
    'en': MODELS_DIR / "vosk-model-small-en-us-0.15",  # English (can recognize Indonesian)
    'ru': MODELS_DIR / "vosk-model-small-ru-0.22",  # Russian
}

# Legacy support - default model path
VOSK_MODEL_PATH = VOSK_MODELS.get(DEFAULT_VOICE_LANGUAGE, MODELS_DIR / "vosk-model-small-en-us-0.15")

# === WHISPER ENGINE (BEST for Indonesian!) ===
# OpenAI Whisper: Free, open source, offline, multi-language
# Excellent Indonesian support (85-95% accuracy)
# Install: pip install openai-whisper torch torchaudio
VOICE_ENGINE = os.getenv("VOICE_ENGINE", "hybrid")  # vosk / whisper / hybrid
DEFAULT_WHISPER_LANGUAGE = os.getenv("DEFAULT_WHISPER_LANGUAGE", "id")  # id/ms/en/ru/auto
WHISPER_MODEL = os.getenv("WHISPER_MODEL", "small")  # tiny/base/small/medium/large
WHISPER_DEVICE = os.getenv("WHISPER_DEVICE", "cpu")  # cpu/cuda
WHISPER_FP16 = os.getenv("WHISPER_FP16", "false").lower() == "true"  # FP16 precision (GPU only)

# Whisper model sizes
WHISPER_MODEL_INFO = {
    'tiny': {'size': '75MB', 'accuracy': '70-75%', 'speed': 'Very fast'},
    'base': {'size': '145MB', 'accuracy': '75-80%', 'speed': 'Fast'},
    'small': {'size': '488MB', 'accuracy': '85-90%', 'speed': 'Medium'},  # RECOMMENDED
    'medium': {'size': '1.5GB', 'accuracy': '90-95%', 'speed': 'Slow'},
    'large': {'size': '3GB', 'accuracy': '95%+', 'speed': 'Very slow'},
}

# Whisper supported languages
WHISPER_LANGUAGES = {
    'id': 'Indonesian',
    'ms': 'Malay', 
    'en': 'English',
    'ru': 'Russian',
    'auto': 'Auto-detect'
}

# Audit Log Path
AUDIT_LOG_PATH = LOGS_DIR / "security_audit.log"
ERROR_LOG_PATH = LOGS_DIR / "errors.log"
