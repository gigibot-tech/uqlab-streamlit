"""API Client with Singleton pattern"""
import requests
from typing import Optional, Dict, Any

class APIClient:
    _instance: Optional['APIClient'] = None
    
    def __init__(self, base_url: str, token: str = ""):
        self.base_url = base_url.rstrip('/')
        self.token = token
    
    @classmethod
    def get_instance(cls, base_url: str, token: str = "") -> 'APIClient':
        if cls._instance is None:
            cls._instance = cls(base_url, token)
        return cls._instance
    
    def _get_headers(self) -> Dict[str, str]:
        headers = {}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers
    
    def get(self, endpoint: str, params: Optional[Dict] = None, timeout: int = 10) -> Any:
        url = f"{self.base_url}{endpoint}"
        response = requests.get(url, params=params, headers=self._get_headers(), timeout=timeout)
        response.raise_for_status()
        return response.json()
    
    def post(self, endpoint: str, data: Dict, timeout: int = 30) -> Any:
        url = f"{self.base_url}{endpoint}"
        response = requests.post(url, json=data, headers=self._get_headers(), timeout=timeout)
        response.raise_for_status()
        return response.json()
    
    def delete(self, endpoint: str, timeout: int = 30) -> Any:
        url = f"{self.base_url}{endpoint}"
        response = requests.delete(url, headers=self._get_headers(), timeout=timeout)
        response.raise_for_status()
        return response.json()
