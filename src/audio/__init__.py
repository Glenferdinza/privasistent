"""Audio module initialization"""

from .text_to_speech import TTSManager
from .speech_recognition import STTManager  
from .wake_word import WakeWordManager

__all__ = ['TTSManager', 'STTManager', 'WakeWordManager']
