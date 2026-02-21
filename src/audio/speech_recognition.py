"""
Speech Recognition Module menggunakan Vosk
Offline, akurat, dan memory efficient
"""

import json
import pyaudio
import vosk
import gc
import logging
from typing import Optional, Callable
import threading

logger = logging.getLogger(__name__)


class SpeechRecognizer:
    """Speech recognizer dengan Vosk untuk akurasi tinggi"""
    
    def __init__(self, model_path: str, sample_rate: int = 16000):
        self.model_path = model_path
        self.sample_rate = sample_rate
        self._model = None
        self._recognizer = None
        self._audio = None
        self._stream = None
        
    def _load_model(self):
        """Load Vosk model"""
        if self._model is None:
            try:
                logger.info(f"Loading Vosk model from {self.model_path}")
                self._model = vosk.Model(str(self.model_path))
                self._recognizer = vosk.KaldiRecognizer(self._model, self.sample_rate)
                self._recognizer.SetWords(True)
                logger.info("Vosk model loaded successfully")
            except Exception as e:
                logger.error(f"Failed to load Vosk model: {e}")
                raise
    
    def _init_audio_stream(self):
        """Inisialisasi audio stream"""
        try:
            self._audio = pyaudio.PyAudio()
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
        
        Args:
            timeout: Waktu maksimal listening dalam detik
            
        Returns:
            Transcript text atau None
        """
        try:
            self._load_model()
            self._init_audio_stream()
            
            logger.info("Listening...")
            frames_read = 0
            max_frames = timeout * self.sample_rate // 4096
            
            while frames_read < max_frames:
                data = self._stream.read(4096, exception_on_overflow=False)
                frames_read += 1
                
                if self._recognizer.AcceptWaveform(data):
                    result = json.loads(self._recognizer.Result())
                    text = result.get('text', '').strip()
                    
                    if text:
                        logger.info(f"Recognized: {text}")
                        return text
            
            # Jika timeout, ambil partial result
            result = json.loads(self._recognizer.FinalResult())
            text = result.get('text', '').strip()
            
            if text:
                logger.info(f"Final result: {text}")
                return text
            
            return None
            
        except Exception as e:
            logger.error(f"Speech recognition error: {e}")
            return None
            
        finally:
            self._cleanup()
    
    def listen_continuous(self, callback: Callable[[str], bool], 
                         energy_threshold: int = 300) -> None:
        """
        Listening mode kontinyu dengan callback
        
        Args:
            callback: Function yang dipanggil setiap ada speech (return True untuk stop)
            energy_threshold: Threshold untuk deteksi speech
        """
        try:
            self._load_model()
            self._init_audio_stream()
            
            logger.info("Continuous listening mode started")
            
            while True:
                data = self._stream.read(4096, exception_on_overflow=False)
                
                if self._recognizer.AcceptWaveform(data):
                    result = json.loads(self._recognizer.Result())
                    text = result.get('text', '').strip()
                    
                    if text:
                        logger.info(f"Detected: {text}")
                        # Cleanup setelah setiap detection
                        del data
                        gc.collect()
                        
                        # Call callback, jika return True maka stop
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
            self._cleanup()
    
    def _cleanup(self):
        """Cleanup resources"""
        try:
            if self._stream:
                self._stream.stop_stream()
                self._stream.close()
                self._stream = None
            
            if self._audio:
                self._audio.terminate()
                self._audio = None
            
            # Keep model loaded untuk reuse (optional)
            # Uncomment jika ingin full cleanup
            # if self._recognizer:
            #     del self._recognizer
            #     self._recognizer = None
            # if self._model:
            #     del self._model
            #     self._model = None
            
            gc.collect()
            logger.info("Audio resources cleaned up")
            
        except Exception as e:
            logger.warning(f"Cleanup warning: {e}")
    
    def __del__(self):
        """Destructor"""
        self._cleanup()
        if self._recognizer:
            del self._recognizer
        if self._model:
            del self._model


class STTManager:
    """Singleton manager untuk Speech Recognition"""
    
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
            from config import VOSK_MODEL_PATH
            self.recognizer = SpeechRecognizer(str(VOSK_MODEL_PATH))
    
    def listen(self, timeout: int = 10) -> Optional[str]:
        """Listen once wrapper"""
        return self.recognizer.listen_once(timeout)
    
    def listen_continuous(self, callback: Callable[[str], bool]) -> None:
        """Continuous listening wrapper"""
        return self.recognizer.listen_continuous(callback)
