"""
Zero-Trust File Access Validator
Strict security layer untuk melindungi sistem file
"""

import os
import logging
from pathlib import Path
from typing import Tuple, List, Optional

logger = logging.getLogger(__name__)


class FileAccessValidator:
    """
    Validator untuk memastikan akses file aman
    Menerapkan prinsip Zero-Trust
    """
    
    def __init__(self, whitelist_dirs: List[Path], blocked_paths: List[Path]):
        """
        Args:
            whitelist_dirs: List direktori yang diizinkan
            blocked_paths: List path yang diblokir
        """
        self.whitelist_dirs = [Path(d).resolve() for d in whitelist_dirs]
        self.blocked_paths = [Path(p).resolve() for p in blocked_paths]
        
        # Pastikan whitelist dirs exist
        for wdir in self.whitelist_dirs:
            wdir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"File access validator initialized")
        logger.info(f"Whitelisted directories: {[str(d) for d in self.whitelist_dirs]}")
        logger.info(f"Blocked paths: {[str(p) for p in self.blocked_paths]}")
    
    def validate_path(self, path_str: str) -> Tuple[bool, Optional[Path], str]:
        """
        Validasi apakah path aman untuk diakses
        
        Args:
            path_str: Path string yang akan divalidasi
            
        Returns:
            Tuple (is_safe, resolved_path, reason)
        """
        try:
            # Resolve path untuk menghindari path traversal
            requested_path = Path(path_str).resolve()
            
            # Check 1: Apakah path dalam blocked paths
            for blocked in self.blocked_paths:
                try:
                    # Check jika requested path adalah child dari blocked path
                    requested_path.relative_to(blocked)
                    reason = f"Akses ditolak: Path berada dalam direktori sistem yang diproteksi"
                    logger.warning(f"BLOCKED ACCESS: {path_str} -> {reason}")
                    return False, None, reason
                except ValueError:
                    # Bukan child dari blocked path, lanjut
                    continue
            
            # Check 2: Apakah path dalam whitelist
            is_whitelisted = False
            for whitelist in self.whitelist_dirs:
                try:
                    # Check jika requested path adalah child dari whitelist
                    requested_path.relative_to(whitelist)
                    is_whitelisted = True
                    break
                except ValueError:
                    continue
            
            if not is_whitelisted:
                reason = f"Akses ditolak: Path tidak ada dalam whitelist yang diizinkan. Sebutkan path secara eksplisit."
                logger.warning(f"NOT WHITELISTED: {path_str} -> {reason}")
                return False, None, reason
            
            # Check 3: Path traversal attack detection
            if '..' in path_str or path_str.startswith('~'):
                reason = f"Akses ditolak: Terdeteksi pola path traversal yang mencurigakan"
                logger.warning(f"PATH TRAVERSAL DETECTED: {path_str}")
                return False, None, reason
            
            # All checks passed
            logger.info(f"ACCESS GRANTED: {path_str}")
            return True, requested_path, "Akses diizinkan"
            
        except Exception as e:
            reason = f"Akses ditolak: Path tidak valid - {str(e)}"
            logger.error(f"PATH VALIDATION ERROR: {path_str} -> {str(e)}")
            return False, None, reason
    
    def validate_and_check_exists(self, path_str: str) -> Tuple[bool, Optional[Path], str]:
        """
        Validasi path dan check apakah exist
        
        Returns:
            Tuple (is_valid, resolved_path, message)
        """
        is_safe, resolved_path, reason = self.validate_path(path_str)
        
        if not is_safe:
            return False, None, reason
        
        # Check existence
        if not resolved_path.exists():
            return False, None, f"Path tidak ditemukan: {path_str}"
        
        return True, resolved_path, "Path valid dan ditemukan"
    
    def is_safe_operation(self, path_str: str, operation: str) -> Tuple[bool, str]:
        """
        Check apakah operasi pada path aman
        
        Args:
            path_str: Path target
            operation: Jenis operasi (read, write, delete, etc)
            
        Returns:
            Tuple (is_safe, reason)
        """
        is_safe, resolved_path, reason = self.validate_path(path_str)
        
        if not is_safe:
            return False, reason
        
        # Additional checks untuk operasi destructive
        if operation in ['delete', 'remove', 'rmdir']:
            # Extra confirmation untuk delete operations
            logger.warning(f"DESTRUCTIVE OPERATION requested: {operation} on {path_str}")
            # Bisa tambahkan additional checks di sini
        
        return True, "Operasi diizinkan"


class SecurityManager:
    """Singleton manager untuk security validation"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not hasattr(self, 'validator'):
            from config import WHITELIST_DIRS, BLOCKED_PATHS
            self.validator = FileAccessValidator(
                whitelist_dirs=WHITELIST_DIRS,
                blocked_paths=BLOCKED_PATHS
            )
    
    def validate(self, path: str) -> Tuple[bool, Optional[Path], str]:
        """Validate path wrapper"""
        return self.validator.validate_path(path)
    
    def check_operation(self, path: str, operation: str) -> Tuple[bool, str]:
        """Check operation safety wrapper"""
        return self.validator.is_safe_operation(path, operation)
