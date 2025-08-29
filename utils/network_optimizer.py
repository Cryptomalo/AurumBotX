
import requests
import time
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
from typing import Dict, Optional

class OptimizedNetworkManager:
    """Manager network ottimizzato"""
    
    def __init__(self):
        self.session = requests.Session()
        
        # Retry strategy
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        
        # HTTP Adapter con connection pooling
        adapter = HTTPAdapter(
            max_retries=retry_strategy,
            pool_connections=10,
            pool_maxsize=20
        )
        
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
        # Headers comuni
        self.session.headers.update({
            'User-Agent': 'AurumBotX/1.0',
            'Connection': 'keep-alive'
        })
    
    def get(self, url: str, timeout: int = 10, **kwargs) -> Optional[requests.Response]:
        """GET ottimizzato"""
        try:
            response = self.session.get(url, timeout=timeout, **kwargs)
            response.raise_for_status()
            return response
        except Exception as e:
            print(f"Network error: {e}")
            return None
    
    def post(self, url: str, timeout: int = 10, **kwargs) -> Optional[requests.Response]:
        """POST ottimizzato"""
        try:
            response = self.session.post(url, timeout=timeout, **kwargs)
            response.raise_for_status()
            return response
        except Exception as e:
            print(f"Network error: {e}")
            return None

# Istanza globale
network_manager = OptimizedNetworkManager()
