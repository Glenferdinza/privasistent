"""
Modul Audio untuk Irma Virtual Assistant
Menangani Text-to-Speech dengan memory management ketat
"""

import pyttsx3
import gc
import logging
from typing import Optional
import threading

logger = logging.getLogger(__name__)


class TextToSpeech:
    """Text-to-Speech engine dengan auto cleanup"""
    
    def __init__(self, rate: int = 175, volume: float = 1.0, gender: str = "female"):
        self.rate = rate
        self.volume = volume
        self.gender = gender
        self._engine = None
        self._lock = threading.Lock()
        
    def _initialize_engine(self) -> pyttsx3.Engine:
        """Inisialisasi engine dengan konfigurasi suara perempuan"""
        try:
            engine = pyttsx3.init('sapi5')
            engine.setProperty('rate', self.rate)
            engine.setProperty('volume', self.volume)
            
            # Pilih suara perempuan dari SAPI5
            voices = engine.getProperty('voices')
            female_voice = None
            
            for voice in voices:
                # Cari voice perempuan (biasanya mengandung 'female' atau 'zira')
                if 'female' in voice.name.lower() or 'zira' in voice.name.lower():
                    female_voice = voice
                    break
                # Fallback ke voice ID 1 (biasanya perempuan di Windows)
                elif voices.index(voice) == 1:
                    female_voice = voice
            
            if female_voice:
                engine.setProperty('voice', female_voice.id)
                logger.info(f"Voice set to: {female_voice.name}")
            else:
                logger.warning("Female voice not found, using default")
            
            return engine
            
        except Exception as e:
            logger.error(f"Failed to initialize TTS engine: {e}")
            raise
    
    def speak(self, text: str, blocking: bool = True) -> bool:
        """
        Ucapkan teks dengan auto cleanup
        
        Args:
            text: Teks yang akan diucapkan
            blocking: Tunggu sampai selesai berbicara
            
        Returns:
            True jika berhasil, False jika gagal
        """
        if not text or not text.strip():
            return False
            
        with self._lock:
            try:
                # Initialize fresh engine
                self._engine = self._initialize_engine()
                
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
    """Singleton manager untuk TTS"""
    
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
            from config import VOICE_RATE, VOICE_VOLUME, VOICE_GENDER
            self.tts = TextToSpeech(
                rate=VOICE_RATE,
                volume=VOICE_VOLUME,
                gender=VOICE_GENDER
            )
    
    def speak(self, text: str, blocking: bool = True) -> bool:
        """Wrapper untuk speak method"""
        return self.tts.speak(text, blocking)
