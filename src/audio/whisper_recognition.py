"""
Whisper Speech Recognition - Alternative engine untuk Indonesian & multi-language
OpenAI Whisper: Open source, gratis, offline, excellent accuracy

Supports: 99+ languages including Indonesian, Malay, English, Russian
"""

import logging
import numpy as np
import pyaudio
import gc
from typing import Optional, List
from pathlib import Path

logger = logging.getLogger(__name__)


class WhisperRecognizer:
    """
    Speech recognizer menggunakan OpenAI Whisper
    Excellent untuk Indonesian language dengan akurasi 85-95%
    
    Models available:
    - tiny (75MB) - Fast, 70-75% accuracy
    - base (145MB) - Balanced, 75-80% accuracy  
    - small (488MB) - Recommended, 85-90% accuracy
    - medium (1.5GB) - High accuracy, 90-95%
    - large (3GB) - Best accuracy, 95%+
    """
    
    SUPPORTED_MODELS = ['tiny', 'base', 'small', 'medium', 'large']
    
    SUPPORTED_LANGUAGES = {
        'id': 'Indonesian',
        'ms': 'Malay',
        'en': 'English',
        'ru': 'Russian',
        'auto': 'Auto-detect'
    }
    
    def __init__(self, model_name: str = 'small', language: str = 'id', 
                 sample_rate: int = 16000):
        """
        Initialize Whisper recognizer
        
        Args:
            model_name: Model size (tiny/base/small/medium/large)
            language: Language code (id/en/ru/ms/auto)
            sample_rate: Audio sample rate
        """
        if model_name not in self.SUPPORTED_MODELS:
            logger.warning(f"Invalid model {model_name}, falling back to 'small'")
            model_name = 'small'
        
        if language not in self.SUPPORTED_LANGUAGES:
            logger.warning(f"Invalid language {language}, falling back to 'id'")
            language = 'id'
        
        self.model_name = model_name
        self.language = language if language != 'auto' else None
        self.sample_rate = sample_rate
        
        self._whisper = None
        self._model = None
        self._audio = None
        self._stream = None
        
        logger.info(f"WhisperRecognizer initialized: model={model_name}, language={language}")
    
    def _load_model(self):
        """Lazy load Whisper model"""
        if self._whisper is None or self._model is None:
            try:
                import whisper
                self._whisper = whisper
                
                logger.info(f"Loading Whisper model: {self.model_name}")
                logger.info("First load may take time to download model...")
                
                # Load model (will download if not exist)
                self._model = whisper.load_model(self.model_name)
                
                logger.info(f"Whisper model '{self.model_name}' loaded successfully")
                
            except ImportError:
                logger.error("Whisper not installed. Install: pip install openai-whisper")
                raise
            except Exception as e:
                logger.error(f"Failed to load Whisper model: {e}")
                raise
    
    def _init_audio_stream(self):
        """Initialize audio stream"""
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
            logger.error(f"Failed to initialize audio: {e}")
            raise
    
    def listen_once(self, duration: int = 5) -> Optional[str]:
        """
        Listen for specified duration and transcribe
        
        Args:
            duration: Recording duration in seconds
            
        Returns:
            Transcribed text or None
        """
        try:
            self._load_model()
            self._init_audio_stream()
            
            logger.info(f"Recording for {duration} seconds...")
            
            # Record audio
            frames = []
            frames_to_read = int(self.sample_rate * duration / 4096)
            
            for _ in range(frames_to_read):
                data = self._stream.read(4096, exception_on_overflow=False)
                frames.append(data)
            
            logger.info("Recording complete, transcribing...")
            
            # Convert to numpy array
            audio_data = b''.join(frames)
            audio_np = np.frombuffer(audio_data, dtype=np.int16).astype(np.float32) / 32768.0
            
            # Transcribe
            result = self._model.transcribe(
                audio_np,
                language=self.language,
                fp16=False  # Use FP32 for CPU compatibility
            )
            
            text = result.get('text', '').strip()
            
            # Cleanup
            del audio_data, audio_np, frames
            gc.collect()
            
            if text:
                logger.info(f"Transcribed: {text}")
                return text
            
            logger.info("No speech detected")
            return None
            
        except Exception as e:
            logger.error(f"Whisper recognition error: {e}")
            return None
        
        finally:
            gc.collect()
    
    def transcribe_file(self, audio_file: str) -> Optional[str]:
        """
        Transcribe audio file
        
        Args:
            audio_file: Path to audio file (mp3/wav/m4a/etc)
            
        Returns:
            Transcribed text or None
        """
        try:
            self._load_model()
            
            audio_path = Path(audio_file)
            if not audio_path.exists():
                logger.error(f"Audio file not found: {audio_file}")
                return None
            
            logger.info(f"Transcribing file: {audio_file}")
            
            result = self._model.transcribe(
                str(audio_path),
                language=self.language,
                fp16=False
            )
            
            text = result.get('text', '').strip()
            
            if text:
                logger.info(f"Transcribed: {text}")
                return text
            
            return None
            
        except Exception as e:
            logger.error(f"File transcription error: {e}")
            return None
    
    def detect_language(self, audio_file: str) -> str:
        """
        Auto-detect language from audio
        
        Args:
            audio_file: Path to audio file
            
        Returns:
            Detected language code
        """
        try:
            self._load_model()
            
            # Load audio
            audio = self._whisper.load_audio(audio_file)
            audio = self._whisper.pad_or_trim(audio)
            
            # Detect language
            mel = self._whisper.log_mel_spectrogram(audio).to(self._model.device)
            _, probs = self._model.detect_language(mel)
            
            detected = max(probs, key=probs.get)
            confidence = probs[detected]
            
            logger.info(f"Detected language: {detected} ({confidence:.2%})")
            return detected
            
        except Exception as e:
            logger.error(f"Language detection error: {e}")
            return 'en'  # Fallback
    
    def switch_language(self, language: str) -> bool:
        """
        Switch recognition language
        
        Args:
            language: Language code (id/en/ru/ms/auto)
            
        Returns:
            True if successful
        """
        if language not in self.SUPPORTED_LANGUAGES:
            logger.error(f"Unsupported language: {language}")
            return False
        
        self.language = language if language != 'auto' else None
        logger.info(f"Language switched to: {self.SUPPORTED_LANGUAGES[language]}")
        return True
    
    def get_supported_languages(self) -> List[str]:
        """Get list of supported languages"""
        return list(self.SUPPORTED_LANGUAGES.keys())
    
    def _cleanup_stream(self):
        """Cleanup audio stream"""
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
            logger.warning(f"Cleanup warning: {e}")
    
    def cleanup(self):
        """Full cleanup including model"""
        self._cleanup_stream()
        
        if self._model:
            del self._model
            self._model = None
        
        if self._whisper:
            self._whisper = None
        
        gc.collect()
        logger.info("Whisper recognizer cleanup complete")
    
    def __del__(self):
        """Destructor"""
        self._cleanup_stream()


class HybridRecognizer:
    """
    Hybrid system: Vosk (fast) + Whisper (accurate)
    Automatically choose best engine based on requirements
    """
    
    def __init__(self, 
                 default_engine: str = 'vosk',
                 vosk_language: str = 'en',
                 whisper_model: str = 'small',
                 whisper_language: str = 'id'):
        """
        Args:
            default_engine: 'vosk' or 'whisper'
            vosk_language: Language for Vosk (en/ru)
            whisper_model: Whisper model size
            whisper_language: Language for Whisper (id/ms/en/ru)
        """
        self.default_engine = default_engine
        self.current_engine = default_engine
        
        # Lazy init recognizers
        self._vosk = None
        self._whisper = None
        
        self.vosk_language = vosk_language
        self.whisper_model = whisper_model
        self.whisper_language = whisper_language
        
        logger.info(f"HybridRecognizer initialized: default={default_engine}")
    
    def listen(self, engine: Optional[str] = None, **kwargs) -> Optional[str]:
        """
        Listen once with specified engine
        
        Args:
            engine: 'vosk', 'whisper', or None (use default)
            **kwargs: Engine-specific parameters
            
        Returns:
            Recognized text
        """
        engine = engine or self.default_engine
        
        if engine == 'vosk':
            return self._listen_vosk(**kwargs)
        elif engine == 'whisper':
            return self._listen_whisper(**kwargs)
        else:
            logger.error(f"Unknown engine: {engine}")
            return None
    
    def _listen_vosk(self, **kwargs) -> Optional[str]:
        """Listen using Vosk"""
        if self._vosk is None:
            from .speech_recognition import SpeechRecognizer
            self._vosk = SpeechRecognizer(default_language=self.vosk_language)
        
        return self._vosk.listen_once(**kwargs)
    
    def _listen_whisper(self, **kwargs) -> Optional[str]:
        """Listen using Whisper"""
        if self._whisper is None:
            self._whisper = WhisperRecognizer(
                model_name=self.whisper_model,
                language=self.whisper_language
            )
        
        return self._whisper.listen_once(**kwargs)
    
    def switch_engine(self, engine: str) -> bool:
        """Switch between engines"""
        if engine not in ['vosk', 'whisper']:
            return False
        
        self.current_engine = engine
        logger.info(f"Engine switched to: {engine}")
        return True
    
    def get_engine_info(self) -> dict:
        """Get current engine info"""
        return {
            'current': self.current_engine,
            'vosk_available': self._vosk is not None,
            'whisper_available': self._whisper is not None,
            'vosk_language': self.vosk_language,
            'whisper_language': self.whisper_language,
            'whisper_model': self.whisper_model
        }


# Export
__all__ = ['WhisperRecognizer', 'HybridRecognizer']
