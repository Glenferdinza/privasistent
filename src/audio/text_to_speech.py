"""
Modul Audio untuk Irma Virtual Assistant
Menangani Text-to-Speech dengan memory management ketat
Multi-language support dengan dynamic voice profiles
"""

import pyttsx3
import gc
import logging
from typing import Optional
import threading
from .voice_language_manager import get_language_manager

logger = logging.getLogger(__name__)


class TextToSpeech:
    """
    Text-to-Speech engine dengan auto cleanup dan multi-language support
    Voice profile akan otomatis berubah sesuai bahasa aktif
    """
    
    def __init__(self, rate: int = 175, volume: float = 1.0, 
                 use_language_manager: bool = True):
        """
        Args:
            rate: Speech rate
            volume: Speech volume (0.0 to 1.0)
            use_language_manager: Auto-switch voice based on language manager
        """
        self.rate = rate
        self.volume = volume
        self.use_language_manager = use_language_manager
        self._engine = None
        self._lock = threading.Lock()
        
        # Get language manager for voice profile switching
        if self.use_language_manager:
            self.lang_manager = get_language_manager()
        
    def _initialize_engine(self, language_code: Optional[str] = None) -> pyttsx3.Engine:
        """
        Inisialisasi engine dengan voice profile sesuai bahasa
        
        Args:
            language_code: Language code untuk voice selection (id/en/ru/ms)
        """
        try:
            engine = pyttsx3.init('sapi5')
            engine.setProperty('rate', self.rate)
            engine.setProperty('volume', self.volume)
            
            # Get all available voices
            voices = engine.getProperty('voices')
            
            # Determine target language
            if self.use_language_manager and language_code is None:
                language_code = self.lang_manager.current_language
            
            # Voice selection berdasarkan bahasa
            voice_mapping = {
                'id': ['id-ID', 'andika', 'indonesian'],  # Indonesian
                'en': ['en-US', 'en-GB', 'zira', 'david', 'english'],  # English
                'ru': ['ru-RU', 'irina', 'russian'],  # Russian
                'ms': ['ms-MY', 'melayu', 'malay']  # Malay
            }
            
            selected_voice = None
            
            # Try to find matching voice for language
            if language_code and language_code in voice_mapping:
                keywords = voice_mapping[language_code]
                
                for voice in voices:
                    voice_name_lower = voice.name.lower()
                    voice_id_lower = voice.id.lower()
                    
                    # Check if any keyword matches
                    if any(keyword.lower() in voice_name_lower or 
                          keyword.lower() in voice_id_lower 
                          for keyword in keywords):
                        selected_voice = voice
                        logger.info(f"Selected voice for {language_code}: {voice.name}")
                        break
            
            # Fallback: use default female voice if language-specific not found
            if selected_voice is None:
                for voice in voices:
                    if 'female' in voice.name.lower() or 'zira' in voice.name.lower():
                        selected_voice = voice
                        logger.info(f"Using fallback voice: {voice.name}")
                        break
                
                # Ultimate fallback: voice index 1
                if selected_voice is None and len(voices) > 1:
                    selected_voice = voices[1]
                    logger.info(f"Using default voice: {voices[1].name}")
            
            # Set selected voice
            if selected_voice:
                engine.setProperty('voice', selected_voice.id)
            
            return engine
            
        except Exception as e:
            logger.error(f"Failed to initialize TTS engine: {e}")
            raise
    
    def speak(self, text: str, blocking: bool = True, 
             language_code: Optional[str] = None) -> bool:
        """
        Ucapkan teks dengan auto cleanup
        Voice profile akan auto-adjust berdasarkan bahasa aktif
        
        Args:
            text: Teks yang akan diucapkan
            blocking: Tunggu sampai selesai berbicara
            language_code: Optional language override (id/en/ru/ms)
            
        Returns:
            True jika berhasil, False jika gagal
        """
        if not text or not text.strip():
            return False
            
        with self._lock:
            try:
                # Initialize engine dengan voice profile yang sesuai
                self._engine = self._initialize_engine(language_code)
                
                logger.info(f"Speaking: {text[:50]}...")
                self._engine.say(text)
                
                if blocking:
                    self._engine.runAndWait()
                else:
                    # Non-blocking mode
                    self._engine.startLoop(False)
                    self._engine.iterate()
                    self._engine.endLoop()
                
                return True
                
            except Exception as e:
                logger.error(f"TTS error: {e}")
                return False
                
            finally:
                # Cleanup langsung setelah selesai
                self._cleanup_engine()
    
    def speak_in_language(self, text: str, language_code: str, 
                         blocking: bool = True) -> bool:
        """
        Speak text dalam bahasa tertentu dengan voice profile yang sesuai
        
        Args:
            text: Text to speak
            language_code: Language code (id/en/ru/ms)
            blocking: Wait until finished
            
        Returns:
            True if successful
        """
        return self.speak(text, blocking=blocking, language_code=language_code)
    
    def _cleanup_engine(self):
        """Hancurkan engine dan bersihkan memory"""
        if self._engine:
            try:
                self._engine.stop()
                del self._engine
                self._engine = None
            except Exception as e:
                logger.warning(f"Engine cleanup warning: {e}")
            finally:
                gc.collect()
    
    def __del__(self):
        """Destructor untuk memastikan cleanup"""
        self._cleanup_engine()


class TTSManager:
    """Singleton manager untuk TTS dengan multi-language support"""
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not hasattr(self, 'tts'):
            from config import VOICE_RATE, VOICE_VOLUME
            self.tts = TextToSpeech(
                rate=VOICE_RATE,
                volume=VOICE_VOLUME,
                use_language_manager=True  # Enable auto-language detection
            )
    
    def speak(self, text: str, blocking: bool = True) -> bool:
        """Wrapper untuk speak method (auto-detect language)"""
        return self.tts.speak(text, blocking)
    
    def speak_in_language(self, text: str, language_code: str, blocking: bool = True) -> bool:
        """Speak dalam bahasa tertentu"""
        return self.tts.speak_in_language(text, language_code, blocking)
