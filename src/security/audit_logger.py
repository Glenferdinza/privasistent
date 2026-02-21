"""
Audit Logger untuk security events
Track semua akses file dan operasi sensitif
"""

import logging
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any
import threading

logger = logging.getLogger(__name__)


class AuditLogger:
    """Logger untuk security audit trail"""
    
    def __init__(self, log_file: Path):
        """
        Args:
            log_file: Path ke file audit log
        """
        self.log_file = Path(log_file)
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        
        logger.info(f"Audit logger initialized: {log_file}")
    
    def log_access_attempt(self, path: str, operation: str, 
                          allowed: bool, reason: str = "") -> None:
        """
        Log file access attempt
        
        Args:
            path: Path yang diakses
            operation: Jenis operasi
            allowed: Apakah akses diizinkan
            reason: Alasan keputusan
        """
        entry = {
            'timestamp': datetime.now().isoformat(),
            'event_type': 'file_access',
            'path': str(path),
            'operation': operation,
            'allowed': allowed,
            'reason': reason
        }
        
        self._write_log(entry)
    
    def log_security_event(self, event_type: str, details: Dict[str, Any]) -> None:
        """
        Log general security event
        
        Args:
            event_type: Tipe event
            details: Detail additional
        """
        entry = {
            'timestamp': datetime.now().isoformat(),
            'event_type': event_type,
            **details
        }
        
        self._write_log(entry)
    
    def log_command(self, command: str, intent: str, executed: bool) -> None:
        """
        Log user command
        
        Args:
            command: Command dari user
            intent: Detected intent
            executed: Apakah command dieksekusi
        """
        entry = {
            'timestamp': datetime.now().isoformat(),
            'event_type': 'user_command',
            'command': command,
            'intent': intent,
            'executed': executed
        }
        
        self._write_log(entry)
    
    def _write_log(self, entry: Dict[str, Any]) -> None:
        """Write log entry to file"""
        with self._lock:
            try:
                with open(self.log_file, 'a', encoding='utf-8') as f:
                    f.write(json.dumps(entry, ensure_ascii=False) + '\n')
            except Exception as e:
                logger.error(f"Failed to write audit log: {e}")
    
    def get_recent_logs(self, count: int = 10) -> list:
        """
        Get recent log entries
        
        Args:
            count: Jumlah entry yang diambil
            
        Returns:
            List of log entries
        """
        try:
            if not self.log_file.exists():
                return []
            
            with open(self.log_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                recent_lines = lines[-count:]
                
                logs = []
                for line in recent_lines:
                    try:
                        logs.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue
                
                return logs
                
        except Exception as e:
            logger.error(f"Failed to read audit log: {e}")
            return []


class AuditManager:
    """Singleton manager untuk audit logging"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not hasattr(self, 'logger'):
            from config import AUDIT_LOG_PATH, AUDIT_LOG_ENABLED
            
            self.enabled = AUDIT_LOG_ENABLED
            if self.enabled:
                self.logger = AuditLogger(AUDIT_LOG_PATH)
            else:
                self.logger = None
    
    def log_access(self, path: str, operation: str, 
                   allowed: bool, reason: str = "") -> None:
        """Log access attempt wrapper"""
        if self.enabled and self.logger:
            self.logger.log_access_attempt(path, operation, allowed, reason)
    
    def log_event(self, event_type: str, details: Dict[str, Any]) -> None:
        """Log security event wrapper"""
        if self.enabled and self.logger:
            self.logger.log_security_event(event_type, details)
    
    def log_command(self, command: str, intent: str, executed: bool) -> None:
        """Log command wrapper"""
        if self.enabled and self.logger:
            self.logger.log_command(command, intent, executed)
