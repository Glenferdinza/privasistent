"""
Resource Monitor untuk tracking CPU, Memory, Disk
Auto-pause jika resource critical
"""

import psutil
import logging
import threading
import time
from typing import Dict, Callable, Optional

logger = logging.getLogger(__name__)


class ResourceMonitor:
    """Monitor resource sistem dengan auto-pause capability"""
    
    def __init__(self, max_memory_percent: int = 80, 
                 max_cpu_percent: int = 90,
                 check_interval: int = 5):
        """
        Args:
            max_memory_percent: Max memory usage sebelum warning
            max_cpu_percent: Max CPU usage sebelum warning
            check_interval: Interval checking dalam detik
        """
        self.max_memory_percent = max_memory_percent
        self.max_cpu_percent = max_cpu_percent
        self.check_interval = check_interval
        
        self._monitoring = False
        self._monitor_thread = None
        self._callbacks = []
        
        logger.info(f"Resource monitor initialized "
                   f"(mem: {max_memory_percent}%, cpu: {max_cpu_percent}%)")
    
    def get_current_stats(self) -> Dict:
        """Dapatkan stats resource saat ini"""
        try:
            # Memory
            mem = psutil.virtual_memory()
            
            # CPU
            cpu_percent = psutil.cpu_percent(interval=0.1)
            
            # Disk
            disk = psutil.disk_usage('/')
            
            # Process info
            process = psutil.Process()
            process_mem = process.memory_info().rss / (1024 * 1024)  # MB
            process_cpu = process.cpu_percent(interval=0.1)
            
            stats = {
                'memory_percent': mem.percent,
                'memory_available_mb': mem.available / (1024 * 1024),
                'cpu_percent': cpu_percent,
                'disk_percent': disk.percent,
                'process_memory_mb': process_mem,
                'process_cpu_percent': process_cpu,
                'is_memory_critical': mem.percent > self.max_memory_percent,
                'is_cpu_critical': cpu_percent > self.max_cpu_percent
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get resource stats: {e}")
            return {'error': str(e)}
    
    def is_resource_available(self) -> tuple[bool, str]:
        """
        Check apakah resource available untuk operasi
        
        Returns:
            Tuple (available, reason)
        """
        stats = self.get_current_stats()
        
        if 'error' in stats:
            return True, "Cannot check resources"
        
        # Check memory
        if stats['is_memory_critical']:
            reason = f"Memory usage tinggi: {stats['memory_percent']:.1f}%"
            logger.warning(reason)
            return False, reason
        
        # Check CPU
        if stats['is_cpu_critical']:
            reason = f"CPU usage tinggi: {stats['cpu_percent']:.1f}%"
            logger.warning(reason)
            return False, reason
        
        return True, "Resources available"
    
    def register_callback(self, callback: Callable[[Dict], None]):
        """
        Register callback yang dipanggil saat resource critical
        
        Args:
            callback: Function yang menerima stats dict
        """
        self._callbacks.append(callback)
        logger.info("Resource monitor callback registered")
    
    def start_monitoring(self):
        """Start background monitoring"""
        if self._monitoring:
            logger.warning("Monitoring already running")
            return
        
        self._monitoring = True
        self._monitor_thread = threading.Thread(
            target=self._monitor_loop,
            daemon=True
        )
        self._monitor_thread.start()
        
        logger.info("Resource monitoring started")
    
    def stop_monitoring(self):
        """Stop background monitoring"""
        self._monitoring = False
        
        if self._monitor_thread:
            self._monitor_thread.join(timeout=2)
        
        logger.info("Resource monitoring stopped")
    
    def _monitor_loop(self):
        """Background monitoring loop"""
        while self._monitoring:
            try:
                stats = self.get_current_stats()
                
                if 'error' not in stats:
                    # Check thresholds
                    if stats['is_memory_critical'] or stats['is_cpu_critical']:
                        logger.warning(f"Resource critical: {stats}")
                        
                        # Call registered callbacks
                        for callback in self._callbacks:
                            try:
                                callback(stats)
                            except Exception as e:
                                logger.error(f"Callback error: {e}")
                
                # Sleep
                time.sleep(self.check_interval)
                
            except Exception as e:
                logger.error(f"Monitor loop error: {e}")
                time.sleep(self.check_interval)
    
    def get_summary(self) -> str:
        """Dapatkan summary resource dalam format human-readable"""
        stats = self.get_current_stats()
        
        if 'error' in stats:
            return "Gagal mendapatkan informasi resource"
        
        summary = f"Memory: {stats['memory_percent']:.1f}% "
        summary += f"(tersedia {stats['memory_available_mb']:.0f}MB), "
        summary += f"CPU: {stats['cpu_percent']:.1f}%, "
        summary += f"Disk: {stats['disk_percent']:.1f}%"
        
        return summary


class ResourceMonitorManager:
    """Singleton manager untuk resource monitor"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not hasattr(self, 'monitor'):
            from config import MAX_MEMORY_PERCENT
            self.monitor = ResourceMonitor(
                max_memory_percent=MAX_MEMORY_PERCENT,
                max_cpu_percent=90,
                check_interval=5
            )
    
    def stats(self) -> Dict:
        """Get stats wrapper"""
        return self.monitor.get_current_stats()
    
    def check(self) -> tuple[bool, str]:
        """Check resource wrapper"""
        return self.monitor.is_resource_available()
    
    def summary(self) -> str:
        """Get summary wrapper"""
        return self.monitor.get_summary()
    
    def start(self):
        """Start monitoring wrapper"""
        self.monitor.start_monitoring()
    
    def stop(self):
        """Stop monitoring wrapper"""
        self.monitor.stop_monitoring()
