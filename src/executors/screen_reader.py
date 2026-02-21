"""
Screen Reader menggunakan OCR
Membaca isi layar yang sedang tampil
"""

import logging
from typing import Tuple, Optional
import gc
import time
from pathlib import Path

logger = logging.getLogger(__name__)


class ScreenReader:
    """Screen reader menggunakan OCR"""
    
    def __init__(self, ocr_language: str = "ind+eng"):
        """
        Args:
            ocr_language: Bahasa untuk OCR (Tesseract format)
        """
        self.ocr_language = ocr_language
        self._pytesseract = None
        self._pil = None
        self._pyautogui = None
        
        logger.info(f"Screen reader initialized with language: {ocr_language}")
    
    def _lazy_import(self):
        """Lazy import heavy libraries"""
        if self._pytesseract is None:
            try:
                import pytesseract
                from PIL import Image
                import pyautogui
                
                self._pytesseract = pytesseract
                self._pil = Image
                self._pyautogui = pyautogui
                
                logger.info("OCR libraries loaded")
            except ImportError as e:
                logger.error(f"Failed to import OCR libraries: {e}")
                raise
    
    def capture_screen(self) -> Tuple[bool, Optional[object]]:
        """
        Capture screenshot layar
        
        Returns:
            Tuple (success, image_or_none)
        """
        try:
            self._lazy_import()
            
            logger.info("Capturing screen...")
            screenshot = self._pyautogui.screenshot()
            
            return True, screenshot
            
        except Exception as e:
            logger.error(f"Failed to capture screen: {e}")
            return False, None
    
    def read_screen(self) -> Tuple[bool, str]:
        """
        Baca isi layar menggunakan OCR
        
        Returns:
            Tuple (success, text_or_error)
        """
        try:
            # Capture screen
            success, screenshot = self.capture_screen()
            
            if not success or screenshot is None:
                return False, "Gagal mengambil screenshot layar"
            
            logger.info("Running OCR on screenshot...")
            
            # Run OCR
            text = self._pytesseract.image_to_string(
                screenshot,
                lang=self.ocr_language
            )
            
            # Cleanup
            del screenshot
            gc.collect()
            
            # Clean text
            text = text.strip()
            
            if not text:
                return False, "Tidak ada text yang terdeteksi di layar"
            
            # Limit length
            max_length = 1500
            if len(text) > max_length:
                text = text[:max_length] + "..."
            
            logger.info(f"OCR completed, found {len(text)} characters")
            return True, text
            
        except Exception as e:
            logger.error(f"Failed to read screen: {e}")
            return False, f"Gagal membaca layar: {str(e)}"
        finally:
            gc.collect()
    
    def read_screen_region(self, x: int, y: int, 
                          width: int, height: int) -> Tuple[bool, str]:
        """
        Baca region tertentu dari layar
        
        Args:
            x, y: Koordinat top-left
            width, height: Ukuran region
            
        Returns:
            Tuple (success, text_or_error)
        """
        try:
            self._lazy_import()
            
            logger.info(f"Capturing screen region: ({x}, {y}, {width}, {height})")
            
            # Capture region
            screenshot = self._pyautogui.screenshot(region=(x, y, width, height))
            
            # Run OCR
            text = self._pytesseract.image_to_string(
                screenshot,
                lang=self.ocr_language
            )
            
            # Cleanup
            del screenshot
            gc.collect()
            
            text = text.strip()
            
            if not text:
                return False, "Tidak ada text yang terdeteksi di region tersebut"
            
            logger.info("Region OCR completed")
            return True, text
            
        except Exception as e:
            logger.error(f"Failed to read screen region: {e}")
            return False, f"Gagal membaca region layar: {str(e)}"
        finally:
            gc.collect()


class ScreenReaderManager:
    """Singleton manager untuk screen reader"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not hasattr(self, 'reader'):
            from config import OCR_LANGUAGE
            self.reader = ScreenReader(ocr_language=OCR_LANGUAGE)
    
    def read(self) -> Tuple[bool, str]:
        """Read screen wrapper"""
        return self.reader.read_screen()
    
    def read_region(self, x: int, y: int, 
                   width: int, height: int) -> Tuple[bool, str]:
        """Read screen region wrapper"""
        return self.reader.read_screen_region(x, y, width, height)
