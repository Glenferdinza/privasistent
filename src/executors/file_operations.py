"""
File Operations Executor
Handle operasi file dengan security validation
"""

import os
import shutil
import logging
from pathlib import Path
from typing import Optional, Tuple
import gc

logger = logging.getLogger(__name__)


class FileOperationsExecutor:
    """Executor untuk operasi file dengan security"""
    
    def __init__(self, security_manager):
        """
        Args:
            security_manager: Instance of SecurityManager
        """
        self.security = security_manager
        from security import AuditManager
        self.audit = AuditManager()
    
    def read_file(self, path_str: str) -> Tuple[bool, str]:
        """
        Baca isi file
        
        Args:
            path_str: Path ke file
            
        Returns:
            Tuple (success, content_or_error)
        """
        # Validate access
        is_safe, resolved_path, reason = self.security.validate(path_str)
        self.audit.log_access(path_str, 'read', is_safe, reason)
        
        if not is_safe:
            logger.warning(f"Read blocked: {path_str}")
            return False, "File tersebut tidak dapat diakses."
        
        try:
            # Check if file exists
            if not resolved_path.exists():
                return False, f"File tidak ditemukan: {path_str}"
            
            if not resolved_path.is_file():
                return False, f"Path bukan sebuah file: {path_str}"
            
            # Check file size
            from config import MAX_FILE_SIZE_MB
            file_size_mb = resolved_path.stat().st_size / (1024 * 1024)
            
            if file_size_mb > MAX_FILE_SIZE_MB:
                return False, f"File terlalu besar untuk dibaca: {file_size_mb:.1f}MB"
            
            # Read file
            with open(resolved_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            logger.info(f"File read successfully: {path_str}")
            return True, content
            
        except Exception as e:
            logger.error(f"Failed to read file {path_str}: {e}")
            return False, f"Gagal membaca file: {str(e)}"
        finally:
            gc.collect()
    
    def list_directory(self, path_str: str) -> Tuple[bool, str]:
        """
        List isi direktori
        
        Args:
            path_str: Path ke direktori
            
        Returns:
            Tuple (success, result_or_error)
        """
        is_safe, resolved_path, reason = self.security.validate(path_str)
        self.audit.log_access(path_str, 'list', is_safe, reason)
        
        if not is_safe:
            return False, "Direktori tersebut tidak dapat diakses."
        
        try:
            if not resolved_path.exists():
                return False, f"Direktori tidak ditemukan: {path_str}"
            
            if not resolved_path.is_dir():
                return False, f"Path bukan sebuah direktori: {path_str}"
            
            # List contents
            items = list(resolved_path.iterdir())
            
            if not items:
                return True, "Direktori kosong."
            
            # Format output
            files = [item.name for item in items if item.is_file()]
            dirs = [item.name for item in items if item.is_dir()]
            
            result = f"Ditemukan {len(dirs)} folder dan {len(files)} file.\n"
            
            if dirs:
                result += f"Folder: {', '.join(dirs[:10])}"
                if len(dirs) > 10:
                    result += f" dan {len(dirs)-10} lainnya"
                result += "\n"
            
            if files:
                result += f"File: {', '.join(files[:10])}"
                if len(files) > 10:
                    result += f" dan {len(files)-10} lainnya"
            
            logger.info(f"Directory listed: {path_str}")
            return True, result
            
        except Exception as e:
            logger.error(f"Failed to list directory {path_str}: {e}")
            return False, f"Gagal membaca direktori: {str(e)}"
        finally:
            gc.collect()
    
    def create_file(self, path_str: str, content: str = "") -> Tuple[bool, str]:
        """
        Buat file baru
        
        Args:
            path_str: Path ke file yang akan dibuat
            content: Isi file (optional)
            
        Returns:
            Tuple (success, message)
        """
        is_safe, resolved_path, reason = self.security.validate(path_str)
        self.audit.log_access(path_str, 'create', is_safe, reason)
        
        if not is_safe:
            return False, "File tersebut tidak dapat dibuat di lokasi tersebut."
        
        try:
            # Check if already exists
            if resolved_path.exists():
                return False, f"File sudah ada: {path_str}"
            
            # Create parent directories if needed
            resolved_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Create file
            with open(resolved_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            logger.info(f"File created: {path_str}")
            return True, f"File berhasil dibuat: {resolved_path.name}"
            
        except Exception as e:
            logger.error(f"Failed to create file {path_str}: {e}")
            return False, f"Gagal membuat file: {str(e)}"
        finally:
            gc.collect()
    
    def delete_file(self, path_str: str) -> Tuple[bool, str]:
        """
        Hapus file (require explicit confirmation)
        
        Args:
            path_str: Path ke file yang akan dihapus
            
        Returns:
            Tuple (success, message)
        """
        is_safe, reason = self.security.check_operation(path_str, 'delete')
        self.audit.log_access(path_str, 'delete', is_safe, reason)
        
        if not is_safe:
            return False, "File tersebut tidak dapat dihapus."
        
        try:
            is_valid, resolved_path, msg = self.security.validator.validate_and_check_exists(path_str)
            
            if not is_valid:
                return False, msg
            
            if not resolved_path.is_file():
                return False, f"Path bukan sebuah file: {path_str}"
            
            # Delete file
            resolved_path.unlink()
            
            logger.info(f"File deleted: {path_str}")
            return True, f"File berhasil dihapus: {resolved_path.name}"
            
        except Exception as e:
            logger.error(f"Failed to delete file {path_str}: {e}")
            return False, f"Gagal menghapus file: {str(e)}"
        finally:
            gc.collect()


class FileOpsManager:
    """Singleton manager untuk file operations"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not hasattr(self, 'executor'):
            from security import SecurityManager
            self.executor = FileOperationsExecutor(SecurityManager())
    
    def read(self, path: str) -> Tuple[bool, str]:
        """Read file wrapper"""
        return self.executor.read_file(path)
    
    def list_dir(self, path: str) -> Tuple[bool, str]:
        """List directory wrapper"""
        return self.executor.list_directory(path)
    
    def create(self, path: str, content: str = "") -> Tuple[bool, str]:
        """Create file wrapper"""
        return self.executor.create_file(path, content)
    
    def delete(self, path: str) -> Tuple[bool, str]:
        """Delete file wrapper"""
        return self.executor.delete_file(path)
