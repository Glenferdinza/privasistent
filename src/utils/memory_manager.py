"""
Memory Manager dengan transient processing
Aggressive memory cleanup setelah setiap operasi
"""

import gc
import logging
import weakref
from typing import Any, Optional
import sys

logger = logging.getLogger(__name__)


class MemoryManager:
    """Manager untuk memory dengan aggressive cleanup"""
    
    def __init__(self, gc_threshold: int = 50, auto_cleanup: bool = True):
        """
        Args:
            gc_threshold: Threshold untuk trigger GC (dalam MB)
            auto_cleanup: Enable auto cleanup
        """
        self.gc_threshold = gc_threshold
        self.auto_cleanup = auto_cleanup
        self._operation_count = 0
        self._weakrefs = []
        
        # Set custom GC thresholds
        gc.set_threshold(700, 10, 10)
        
        logger.info(f"Memory manager initialized (threshold: {gc_threshold}MB)")
    
    def cleanup(self, aggressive: bool = False) -> dict:
        """
        Cleanup memory
        
        Args:
            aggressive: Perform aggressive cleanup
            
        Returns:
            Dict dengan stats cleanup
        """
        try:
            # Get memory before cleanup
            import psutil
            process = psutil.Process()
            mem_before = process.memory_info().rss / (1024 * 1024)  # MB
            
            # Run garbage collection
            if aggressive:
                # Full collection pada semua generasi
                collected = sum([gc.collect(generation) for generation in range(3)])
            else:
                # Standard collection
                collected = gc.collect()
            
            # Get memory after cleanup
            mem_after = process.memory_info().rss / (1024 * 1024)  # MB
            freed = mem_before - mem_after
            
            stats = {
                'objects_collected': collected,
                'memory_before_mb': mem_before,
                'memory_after_mb': mem_after,
                'memory_freed_mb': freed
            }
            
            logger.info(f"Memory cleanup: {collected} objects collected, "
                       f"{freed:.1f}MB freed")
            
            return stats
            
        except Exception as e:
            logger.error(f"Memory cleanup error: {e}")
            return {'error': str(e)}
    
    def cleanup_after_operation(self):
        """Cleanup setelah operasi (called automatically)"""
        self._operation_count += 1
        
        if self.auto_cleanup:
            # Cleanup setiap 5 operasi
            if self._operation_count % 5 == 0:
                self.cleanup()
    
    def get_memory_usage(self) -> dict:
        """Dapatkan informasi memory usage"""
        try:
            import psutil
            
            # Process memory
            process = psutil.Process()
            mem_info = process.memory_info()
            
            # System memory
            system_mem = psutil.virtual_memory()
            
            usage = {
                'process_rss_mb': mem_info.rss / (1024 * 1024),
                'process_vms_mb': mem_info.vms / (1024 * 1024),
                'system_used_percent': system_mem.percent,
                'system_available_mb': system_mem.available / (1024 * 1024)
            }
            
            return usage
            
        except Exception as e:
            logger.error(f"Failed to get memory usage: {e}")
            return {'error': str(e)}
    
    def is_memory_critical(self) -> bool:
        """Check apakah memory dalam kondisi critical"""
        try:
            usage = self.get_memory_usage()
            
            if 'error' in usage:
                return False
            
            # Critical jika system memory > 80%
            return usage['system_used_percent'] > 80
            
        except Exception as e:
            logger.error(f"Failed to check memory: {e}")
            return False
    
    def register_object(self, obj: Any) -> weakref.ref:
        """
        Register object dengan weak reference untuk tracking
        
        Args:
            obj: Object yang akan ditrack
            
        Returns:
            Weak reference ke object
        """
        weak_ref = weakref.ref(obj, self._on_object_deleted)
        self._weakrefs.append(weak_ref)
        return weak_ref
    
    def _on_object_deleted(self, weak_ref):
        """Callback ketika object dihapus"""
        try:
            self._weakrefs.remove(weak_ref)
            logger.debug("Tracked object deleted")
        except ValueError:
            pass
    
    def force_delete(self, *objects):
        """
        Force delete objects dan cleanup
        
        Args:
            *objects: Objects yang akan dihapus
        """
        for obj in objects:
            try:
                del obj
            except Exception as e:
                logger.warning(f"Failed to delete object: {e}")
        
        self.cleanup(aggressive=True)


class MemoryManagerSingleton:
    """Singleton manager untuk memory management"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not hasattr(self, 'manager'):
            from config import GC_THRESHOLD, AUTO_CLEANUP_ENABLED
            self.manager = MemoryManager(
                gc_threshold=GC_THRESHOLD,
                auto_cleanup=AUTO_CLEANUP_ENABLED
            )
    
    def cleanup(self, aggressive: bool = False) -> dict:
        """Cleanup wrapper"""
        return self.manager.cleanup(aggressive)
    
    def after_operation(self):
        """After operation wrapper"""
        self.manager.cleanup_after_operation()
    
    def usage(self) -> dict:
        """Get memory usage wrapper"""
        return self.manager.get_memory_usage()
    
    def is_critical(self) -> bool:
        """Check critical wrapper"""
        return self.manager.is_memory_critical()
