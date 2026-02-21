"""
Voice Language Manager - Multi-Language Switching dengan Lazy Loading
Efficient memory management untuk 2 bahasa: English, Russian

NOTE: Indonesian & Malay models tidak tersedia di Vosk.
English model dapat recognize Indonesian words dengan akurasi moderate (~60-70%).

CRITICAL RULES:
- HANYA 1 model loaded di RAM pada satu waktu
- Forced memory cleanup sebelum load model baru
- No zombie processes
"""

import gc
import logging
from pathlib import Path
from typing import Optional, Dict
import threading
import vosk
import pyaudio

logger = logging.getLogger(__name__)


class VoiceLanguageManager:
    """
    Manager untuk switching bahasa dengan lazy loading
    Ensures only ONE language model in memory at a time
    """
    
    # Available languages (ONLY models that exist in Vosk)
    # NOTE: Indonesian & Malay models DO NOT EXIST in Vosk repository
    # English model can recognize Indonesian words with moderate accuracy
    LANGUAGES = {
        'en': {
            'name': 'English (+ Indonesian recognition)',
            'model_path': 'models/vosk-model-small-en-us-0.15',
            'tts_voice_id': 'HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft\\Speech\\Voices\\Tokens\\TTS_MS_EN-US_ZIRA_11.0',
            'switch_keywords': [
                'switch to english',
                'change language english',
                'use english',
                'english language',
                'ganti bahasa inggris',
                'english mode',
                'bahasa inggris'
            ],
            'description': 'Universal model - can recognize English and Indonesian'
        },
        'ru': {
            'name': 'Russian',
            'model_path': 'models/vosk-model-small-ru-0.22',
            'tts_voice_id': 'HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft\\Speech\\Voices\\Tokens\\TTS_MS_RU-RU_IRINA_11.0',
            'switch_keywords': [
                'переключить на русский',
                'смени язык русский',
                'русский язык',
                'switch to russian',
                'ganti bahasa rusia',
                'russian mode'
            ],
            'description': 'Russian language model'
        }
    }
    
    def __init__(self, default_language: str = 'id', sample_rate: int = 16000):
        """
        Initialize language manager
        
        Args:
            default_language: Default language code (id/en/ru/ms)
            sample_rate: Audio sample rate
        """
        self.current_language = default_language
        self.sample_rate = sample_rate
        
        # Active model references (will be set to None after cleanup)
        self._active_model: Optional[vosk.Model] = None
        self._active_recognizer: Optional[vosk.KaldiRecognizer] = None
        
        # Lock for thread safety
        self._lock = threading.Lock()
        en
        # Model loaded flag
        self._is_loaded = False
        
        logger.info(f"VoiceLanguageManager initialized with default: {default_language}")
    
    def load_language(self, language_code: str) -> bool:
        """
        Load specific language model dengan forced cleanup model lama
        
        Args:
            language_code: Language code (id/en/ru/ms)
            
        Returns:
            True if successful, False otherwise
        """
        with self._lock:
            if language_code not in self.LANGUAGES:
                logger.error(f"Invalid language code: {language_code}")
                return False
            
            lang_info = self.LANGUAGES[language_code]
            model_path = Path(lang_info['model_path'])
            
            if not model_path.exists():
                logger.error(f"Model path not found: {model_path}")
                return False
            
            try:
                # STEP 1: FORCED CLEANUP of old model
                if self._is_loaded:
                    logger.info(f"Unloading previous model: {self.current_language}")
                    self._force_cleanup()
                
                # STEP 2: Load new model
                logger.info(f"Loading {lang_info['name']} model from {model_path}")
                
                self._active_model = vosk.Model(str(model_path))
                self._active_recognizer = vosk.KaldiRecognizer(
                    self._active_model, 
                    self.sample_rate
                )
                self._active_recognizer.SetWords(True)
                
                # Update state
                self.current_language = language_code
                self._is_loaded = True
                
                logger.info(f"✓ {lang_info['name']} model loaded successfully")
                logger.info(f"Memory status: Model active for {language_code}")
                
                return True
                
            except Exception as e:
                logger.error(f"Failed to load {language_code} model: {e}")
                self._force_cleanup()
                return False
    
    def _force_cleanup(self):
        """
        FORCED memory cleanup - menghapus model dari RAM
        Critical untuk mencegah memory leak
        """
        try:
            logger.info("Starting FORCED memory cleanup...")
            
            # Delete recognizer first (depends on model)
            if self._active_recognizer is not None:
                del self._active_recognizer
                self._active_recognizer = None
                logger.debug("✓ KaldiRecognizer deleted")
            
            # Delete model
            if self._active_model is not None:
                del self._active_model
                self._active_model = None
                logger.debug("✓ Vosk Model deleted")
            
            # Force garbage collection
            collected = gc.collect()
            logger.info(f"✓ gc.collect() executed - collected {collected} objects")
            
            self._is_loaded = False
            logger.info("✓ Memory cleanup completed")
            
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
    
    def switch_language(self, language_code: str) -> tuple[bool, str]:
        """
        Switch to different language dengan full cleanup
        
        Args:
            language_code: Target language (id/en/ru/ms)
            
        Returns:
            Tuple (success: bool, message: str)
        """
        if language_code == self.current_language:
            lang_name = self.LANGUAGES[language_code]['name']
            return True, f"Already using {lang_name}"
        
        if language_code not in self.LANGUAGES:
            return False, f"Unknown language: {language_code}"
        
        lang_name = self.LANGUAGES[language_code]['name']
        logger.info(f"Switching language: {self.current_language} → {language_code}")
        
        success = self.load_language(language_code)
        
        if success:
            # Confirmation messages in target language
            messages = {
                'id': f"Bahasa telah diganti ke {lang_name}. Saya siap membantu Anda.",
                'en': f"Language switched to {lang_name}. I'm ready to assist you.",
                'ru': f"Язык изменён на {lang_name}. Я готов помочь вам.",
                'ms': f"Bahasa telah ditukar ke {lang_name}. Saya bersedia membantu anda."
            }
            return True, messages.get(language_code, f"Switched to {lang_name}")
        else:
            return False, f"Failed to switch to {lang_name}"
    
    def detect_language_switch_command(self, text: str) -> Optional[str]:
        """
        Detect language switch keyword dari speech input
        
        Args:
            text: Recognized speech text
            
        Returns:
            Target language code if detected, None otherwise
        """
        text_lower = text.lower().strip()
        
        # Check all languages for switch keywords
        for lang_code, lang_info in self.LANGUAGES.items():
            for keyword in lang_info['switch_keywords']:
                if keyword in text_lower:
                    logger.info(f"Language switch detected: '{text}' → {lang_code}")
                    return lang_code
        
        return None
    
    def get_recognizer(self) -> Optional[vosk.KaldiRecognizer]:
        """Get active recognizer instance"""
        if not self._is_loaded:
            logger.warning("No model loaded yet")
            return None
        return self._active_recognizer
    
    def get_tts_voice_id(self) -> str:
        """Get TTS voice ID for current language"""
        return self.LANGUAGES[self.current_language]['tts_voice_id']
    
    def get_current_language_name(self) -> str:
        """Get current language name"""
        return self.LANGUAGES[self.current_language]['name']
    
    def is_model_loaded(self) -> bool:
        """Check if model is currently loaded"""
        return self._is_loaded
    
    def get_available_languages(self) -> Dict[str, str]:
        """Get dict of available languages"""
        return {code: info['name'] for code, info in self.LANGUAGES.items()}
    
    def cleanup(self):
        """Final cleanup on shutdown"""
        logger.info("Shutting down VoiceLanguageManager...")
        self._force_cleanup()
        logger.info("VoiceLanguageManager shutdown complete")


# Global instance (singleton pattern)
_language_manager: Optional[VoiceLanguageManager] = None
_manager_lock = threading.Lock()


def get_language_manager(default_lang: str = 'id') -> VoiceLanguageManager:
    """
    Get or create global language manager instance (singleton)
    
    Args:
        default_lang: Default language if creating new instance
        
    Returns:
        VoiceLanguageManager instance
    """
    global _language_manager
    
    with _manager_lock:
        if _language_manager is None:
            _language_manager = VoiceLanguageManager(default_language=default_lang)
        return _language_manager


# Export
__all__ = ['VoiceLanguageManager', 'get_language_manager']
