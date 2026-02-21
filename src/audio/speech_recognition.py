"""
Speech Recognition Module menggunakan Vosk
Multi-language support dengan dynamic switching dan lazy loading
Offline, akurat, dan memory efficient
"""

import json
import pyaudio
import vosk
import gc
import logging
from typing import Optional, Callable
import threading
from .voice_language_manager import get_language_manager

logger = logging.getLogger(__name__)


class SpeechRecognizer:
    """
    Speech recognizer dengan Vosk dan multi-language support
    Menggunakan VoiceLanguageManager untuk efficient memory management
    """
    
    def __init__(self, default_language: str = 'id', sample_rate: int = 16000):
        """
        Args:
            default_language: Default language code (id/en/ru/ms)
            sample_rate: Audio sample rate
        """
        self.sample_rate = sample_rate
        self._audio = None
        self._stream = None
        
        # Get language manager instance
        self.lang_manager = get_language_manager(default_lang=default_language)
        
        # Load default language on startup
        logger.info(f"Initializing speech recognizer with language: {default_language}")
        if not self.lang_manager.is_model_loaded():
            self.lang_manager.load_language(default_language)
    
    def _init_audio_stream(self):
        """Inisialisasi audio stream"""
        try:
            if self._audio is None:
                self._audio = pyaudio.PyAudio()
            
            if self._stream is None:
                self._stream = self._audio.open(
                    format=pyaudio.paInt16,
                    channels=1,
                    rate=self.sample_rate,
                    input=True,
                    frames_per_buffer=4096
                )
                logger.info("Audio stream initialized")
        except Exception as e:
            logger.error(f"Failed to initialize audio stream: {e}")
            raise
    
    def listen_once(self, timeout: int = 10) -> Optional[str]:
        """
        Dengarkan sekali dan return transcript
        Otomatis detect language switch command
        
        Args:
            timeout: Waktu maksimal listening dalam detik
            
        Returns:
            Transcript text atau None
        """
        try:
            self._init_audio_stream()
            
            recognizer = self.lang_manager.get_recognizer()
            if recognizer is None:
                logger.error("No recognizer available")
                return None
            
            logger.info(f"Listening... (language: {self.lang_manager.get_current_language_name()})")
            frames_read = 0
            max_frames = timeout * self.sample_rate // 4096
            
            while frames_read < max_frames:
                data = self._stream.read(4096, exception_on_overflow=False)
                frames_read += 1
                
                if recognizer.AcceptWaveform(data):
                    result = json.loads(recognizer.Result())
                    text = result.get('text', '').strip()
                    
                    if text:
                        logger.info(f"Recognized: {text}")
                        
                        # Check for language switch command
                        target_lang = self.lang_manager.detect_language_switch_command(text)
                        if target_lang:
                            # Switch language
                            success, message = self.lang_manager.switch_language(target_lang)
                            if success:
                                # Return switch confirmation message
                                return f"__LANG_SWITCH__:{message}"
                            else:
                                logger.error(f"Language switch failed: {message}")
                        
                        return text
                
                # Cleanup buffer
                del data
            
            # Jika timeout, ambil partial result
            result = json.loads(recognizer.FinalResult())
            text = result.get('text', '').strip()
            
            if text:
                logger.info(f"Final result: {text}")
                
                # Check language switch in final result too
                target_lang = self.lang_manager.detect_language_switch_command(text)
                if target_lang:
                    success, message = self.lang_manager.switch_language(target_lang)
                    if success:
                        return f"__LANG_SWITCH__:{message}"
                
                return text
            
            return None
            
        except Exception as e:
            logger.error(f"Speech recognition error: {e}")
            return None
        
        finally:
            gc.collect()
    
    def listen_continuous(self, callback: Callable[[str], bool], 
                         check_language_switch: bool = True) -> None:
        """
        Listening mode kontinyu dengan callback
        Otomatis handle language switching
        
        Args:
            callback: Function yang dipanggil setiap ada speech (return True untuk stop)
            check_language_switch: Auto-detect dan handle language switch commands
        """
        try:
            self._init_audio_stream()
            
            logger.info("Continuous listening mode started")
            logger.info(f"Current language: {self.lang_manager.get_current_language_name()}")
            
            while True:
                recognizer = self.lang_manager.get_recognizer()
                if recognizer is None:
                    logger.error("No recognizer available, stopping")
                    break
                
                data = self._stream.read(4096, exception_on_overflow=False)
                
                if recognizer.AcceptWaveform(data):
                    result = json.loads(recognizer.Result())
                    text = result.get('text', '').strip()
                    
                    if text:
                        logger.info(f"Detected: {text}")
                        
                        # Cleanup buffer
                        del data
                        gc.collect()
                        
                        # Check for language switch
                        if check_language_switch:
                            target_lang = self.lang_manager.detect_language_switch_command(text)
                            if target_lang:
                                success, message = self.lang_manager.switch_language(target_lang)
                                logger.info(f"Language switched: {message}")
                                # Continue listening in new language
                                continue
                        
                        # Call callback dengan text
                        # Return True dari callback akan stop listening
                        if callback(text):
                            break
                else:
                    # Cleanup buffer setiap iterasi
                    del data
                    
        except KeyboardInterrupt:
            logger.info("Listening stopped by user")
        except Exception as e:
            logger.error(f"Continuous listening error: {e}")
        finally:
            self._cleanup_stream()
    
    def switch_language(self, language_code: str) -> bool:
        """
        Manually switch language
        
        Args:
            language_code: Target language (id/en/ru/ms)
            
        Returns:
            True if successful
        """
        success, message = self.lang_manager.switch_language(language_code)
        logger.info(message)
        return success
    
    def get_current_language(self) -> str:
        """Get current language code"""
        return self.lang_manager.current_language
    
    def get_available_languages(self):
        """Get available languages"""
        return self.lang_manager.get_available_languages()
    
    def _cleanup_stream(self):
        """Cleanup audio stream only (keep model loaded)"""
        try:
            if self._stream:
                self._stream.stop_stream()
                self._stream.close()
                self._stream = None
            
            if self._audio:
                self._audio.terminate()
                self._audio = None
            
            gc.collect()
            logger.info("Audio stream cleaned up")
            
        except Exception as e:
            logger.warning(f"Stream cleanup warning: {e}")
    
    def cleanup(self):
        """Full cleanup including language manager"""
        self._cleanup_stream()
        self.lang_manager.cleanup()
    
    def __del__(self):
        """Destructor"""
        self._cleanup_stream()


class STTManager:
    """Singleton manager untuk Speech Recognition dengan multi-language support"""
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not hasattr(self, 'recognizer'):
            # Get default language from config
            try:
                from config import DEFAULT_VOICE_LANGUAGE
                default_lang = DEFAULT_VOICE_LANGUAGE
            except ImportError:
                default_lang = 'id'  # Fallback to Indonesian
            
            self.recognizer = SpeechRecognizer(default_language=default_lang)
            logger.info(f"STTManager initialized with language: {default_lang}")
    
    def listen(self, timeout: int = 10) -> Optional[str]:
        """Listen once wrapper"""
        return self.recognizer.listen_once(timeout)
    
    def listen_continuous(self, callback: Callable[[str], bool]) -> None:
        """Continuous listening wrapper"""
        return self.recognizer.listen_continuous(callback)
    
    def switch_language(self, language_code: str) -> bool:
        """Switch language wrapper"""
        return self.recognizer.switch_language(language_code)
    
    def get_current_language(self) -> str:
        """Get current language"""
        return self.recognizer.get_current_language()
    
    def get_available_languages(self):
        """Get available languages"""
        return self.recognizer.get_available_languages()
