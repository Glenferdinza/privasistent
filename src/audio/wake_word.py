"""
Wake Word Detection untuk Irma
Deteksi keyword "hey irma" atau "halo irma" dari continuous audio stream
"""

import logging
from typing import Optional
import re

logger = logging.getLogger(__name__)


class WakeWordDetector:
    """
    Simple wake word detector menggunakan keyword matching
    Untuk production bisa diganti dengan Porcupine atau Snowboy
    """
    
    def __init__(self, wake_words: list = None, sensitivity: float = 0.5):
        """
        Args:
            wake_words: List kata pemicu (default: ["hey irma", "halo irma"])
            sensitivity: Sensitivitas matching (tidak digunakan di versi simple ini)
        """
        self.wake_words = wake_words or ["hey irma", "halo irma", "hai irma"]
        self.sensitivity = sensitivity
        
        # Compile regex patterns untuk matching yang lebih flexible
        self.patterns = [
            re.compile(r'\b' + re.escape(word) + r'\b', re.IGNORECASE)
            for word in self.wake_words
        ]
        
        logger.info(f"Wake word detector initialized with: {self.wake_words}")
    
    def detect(self, text: str) -> bool:
        """
        Deteksi apakah text mengandung wake word
        
        Args:
            text: Text hasil speech recognition
            
        Returns:
            True jika wake word terdeteksi
        """
        if not text:
            return False
        
        text_lower = text.lower().strip()
        
        # Check dengan pattern matching
        for pattern in self.patterns:
            if pattern.search(text_lower):
                logger.info(f"Wake word detected in: {text}")
                return True
        
        return False
    
    def extract_command(self, text: str) -> Optional[str]:
        """
        Extract command setelah wake word
        
        Args:
            text: Full text dengan wake word
            
        Returns:
            Command text tanpa wake word, atau None
        """
        if not self.detect(text):
            return None
        
        text_lower = text.lower()
        
        # Cari posisi wake word dan ambil text setelahnya
        for wake_word in self.wake_words:
            if wake_word in text_lower:
                # Split dan ambil semua setelah wake word
                parts = text_lower.split(wake_word, 1)
                if len(parts) > 1:
                    command = parts[1].strip()
                    if command:
                        logger.info(f"Command extracted: {command}")
                        return command
        
        return None


class WakeWordManager:
    """Singleton manager untuk wake word detection"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not hasattr(self, 'detector'):
            from config import WAKE_WORD, WAKE_WORD_SENSITIVITY
            
            # Parse wake words jika comma-separated
            wake_words = [w.strip() for w in WAKE_WORD.split(',')]
            
            self.detector = WakeWordDetector(
                wake_words=wake_words,
                sensitivity=WAKE_WORD_SENSITIVITY
            )
    
    def detect(self, text: str) -> bool:
        """Detect wake word wrapper"""
        return self.detector.detect(text)
    
    def extract_command(self, text: str) -> Optional[str]:
        """Extract command wrapper"""
        return self.detector.extract_command(text)
