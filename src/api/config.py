"""
Configuration management for API keys and settings.
"""

import os
import secrets
from pathlib import Path
from typing import Optional


class Config:
    """Application configuration."""
    
    # API Key for authentication
    API_KEY: Optional[str] = os.getenv("API_KEY")
    
    # If no API_KEY is set, generate one and save to .env
    @classmethod
    def ensure_api_key(cls) -> str:
        """Ensure API key exists, generate if needed."""
        if cls.API_KEY:
            return cls.API_KEY
        
        # Try to load from config/.env file
        env_file = Path(__file__).parent.parent.parent / "config" / ".env"
        if env_file.exists():
            with open(env_file) as f:
                for line in f:
                    if line.startswith("API_KEY="):
                        key = line.strip().split("=", 1)[1]
                        cls.API_KEY = key
                        return key
        
        # Generate new API key
        new_key = secrets.token_urlsafe(32)
        
        # Ensure config directory exists
        env_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Save to .env
        with open(env_file, "a") as f:
            f.write(f"\nAPI_KEY={new_key}\n")
        
        cls.API_KEY = new_key
        print(f"[INFO] Generated new API key: {new_key}")
        print(f"[INFO] Saved to {env_file}")
        
        return new_key


# Initialize configuration
config = Config()
