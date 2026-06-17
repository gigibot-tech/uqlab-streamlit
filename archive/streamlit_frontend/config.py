"""Application Configuration"""
import os
from dataclasses import dataclass

@dataclass
class AppConfig:
    api_url: str
    api_token: str
    
    def __init__(self):
        self.api_url = os.getenv("API_URL", "http://localhost:8000")
        self.api_token = os.getenv("API_TOKEN", "")
    
    @property
    def has_auth(self) -> bool:
        return bool(self.api_token)
