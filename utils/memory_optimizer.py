# Copyright (c) 2025 AurumBotX
# SPDX-License-Identifier: MIT


import psutil
import gc
import logging
from typing import Dict

class MemoryOptimizer:
    """Ottimizzatore memoria"""
    
    def __init__(self):
        self.logger = logging.getLogger('MemoryOptimizer')
    
    def get_memory_usage(self) -> Dict:
        """Ottieni uso memoria corrente"""
        process = psutil.Process()
        memory_info = process.memory_info()
        
        return {
            'rss_mb': memory_info.rss / 1024 / 1024,
            'vms_mb': memory_info.vms / 1024 / 1024,
            'percent': process.memory_percent(),
            'available_mb': psutil.virtual_memory().available / 1024 / 1024
        }
    
    def optimize_memory(self) -> Dict:
        """Ottimizza memoria"""
        before = self.get_memory_usage()
        
        # Garbage collection forzato
        collected = gc.collect()
        
        after = self.get_memory_usage()
        
        return {
            'before_mb': before['rss_mb'],
            'after_mb': after['rss_mb'],
            'freed_mb': before['rss_mb'] - after['rss_mb'],
            'objects_collected': collected
        }
    
    def monitor_memory(self, threshold_mb: float = 500) -> bool:
        """Monitora memoria e ottimizza se necessario"""
        usage = self.get_memory_usage()
        
        if usage['rss_mb'] > threshold_mb:
            self.logger.warning(f"Memoria alta: {usage['rss_mb']:.1f}MB")
            result = self.optimize_memory()
            self.logger.info(f"Memoria liberata: {result['freed_mb']:.1f}MB")
            return True
        
        return False

# Istanza globale
memory_optimizer = MemoryOptimizer()
