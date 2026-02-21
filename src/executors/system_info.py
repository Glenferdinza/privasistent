"""
System Information Executor
Mengambil informasi sistem
"""

import psutil
import platform
import logging
from datetime import datetime
from typing import Dict
import gc

logger = logging.getLogger(__name__)


class SystemInfoExecutor:
    """Executor untuk mendapatkan informasi sistem"""
    
    def __init__(self):
        pass
    
    def get_memory_info(self) -> str:
        """Dapatkan informasi memory"""
        try:
            mem = psutil.virtual_memory()
            
            total_gb = mem.total / (1024**3)
            used_gb = mem.used / (1024**3)
            available_gb = mem.available / (1024**3)
            percent = mem.percent
            
            info = f"Memory: {used_gb:.1f}GB / {total_gb:.1f}GB digunakan ({percent}%). "
            info += f"Tersedia: {available_gb:.1f}GB"
            
            return info
            
        except Exception as e:
            logger.error(f"Failed to get memory info: {e}")
            return "Gagal mendapatkan informasi memory"
        finally:
            gc.collect()
    
    def get_cpu_info(self) -> str:
        """Dapatkan informasi CPU"""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_count = psutil.cpu_count(logical=True)
            cpu_freq = psutil.cpu_freq()
            
            info = f"CPU: {cpu_percent}% digunakan. "
            info += f"{cpu_count} core. "
            
            if cpu_freq:
                info += f"Frequency: {cpu_freq.current:.0f}MHz"
            
            return info
            
        except Exception as e:
            logger.error(f"Failed to get CPU info: {e}")
            return "Gagal mendapatkan informasi CPU"
        finally:
            gc.collect()
    
    def get_disk_info(self) -> str:
        """Dapatkan informasi disk"""
        try:
            disk = psutil.disk_usage('/')
            
            total_gb = disk.total / (1024**3)
            used_gb = disk.used / (1024**3)
            free_gb = disk.free / (1024**3)
            percent = disk.percent
            
            info = f"Disk: {used_gb:.1f}GB / {total_gb:.1f}GB digunakan ({percent}%). "
            info += f"Tersedia: {free_gb:.1f}GB"
            
            return info
            
        except Exception as e:
            logger.error(f"Failed to get disk info: {e}")
            return "Gagal mendapatkan informasi disk"
        finally:
            gc.collect()
    
    def get_system_info(self) -> str:
        """Dapatkan informasi sistem lengkap"""
        try:
            system = platform.system()
            release = platform.release()
            version = platform.version()
            machine = platform.machine()
            processor = platform.processor()
            
            info = f"Sistem: {system} {release}. "
            info += f"Arsitektur: {machine}. "
            info += f"Processor: {processor}"
            
            return info
            
        except Exception as e:
            logger.error(f"Failed to get system info: {e}")
            return "Gagal mendapatkan informasi sistem"
        finally:
            gc.collect()
    
    def get_time_info(self) -> str:
        """Dapatkan informasi waktu"""
        try:
            now = datetime.now()
            
            # Format Indonesia
            days = ['Senin', 'Selasa', 'Rabu', 'Kamis', 'Jumat', 'Sabtu', 'Minggu']
            months = ['Januari', 'Februari', 'Maret', 'April', 'Mei', 'Juni',
                     'Juli', 'Agustus', 'September', 'Oktober', 'November', 'Desember']
            
            day_name = days[now.weekday()]
            month_name = months[now.month - 1]
            
            info = f"Sekarang {day_name}, {now.day} {month_name} {now.year}. "
            info += f"Pukul {now.hour:02d}:{now.minute:02d}"
            
            return info
            
        except Exception as e:
            logger.error(f"Failed to get time info: {e}")
            return "Gagal mendapatkan informasi waktu"
    
    def get_all_info(self) -> str:
        """Dapatkan semua informasi sistem"""
        info_parts = [
            self.get_system_info(),
            self.get_memory_info(),
            self.get_cpu_info(),
            self.get_disk_info()
        ]
        
        return " | ".join(info_parts)


class SystemInfoManager:
    """Singleton manager untuk system info"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not hasattr(self, 'executor'):
            self.executor = SystemInfoExecutor()
    
    def memory(self) -> str:
        """Get memory info wrapper"""
        return self.executor.get_memory_info()
    
    def cpu(self) -> str:
        """Get CPU info wrapper"""
        return self.executor.get_cpu_info()
    
    def disk(self) -> str:
        """Get disk info wrapper"""
        return self.executor.get_disk_info()
    
    def system(self) -> str:
        """Get system info wrapper"""
        return self.executor.get_system_info()
    
    def time(self) -> str:
        """Get time info wrapper"""
        return self.executor.get_time_info()
    
    def all(self) -> str:
        """Get all info wrapper"""
        return self.executor.get_all_info()
