import os
from typing import List
from dotenv import load_dotenv

load_dotenv()

class Settings:
    # Supabase
    SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
    SUPABASE_KEY: str = os.getenv("SUPABASE_KEY", "")
    SUPABASE_JWT_SECRET: str = os.getenv("SUPABASE_JWT_SECRET", "")
    
    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-here")
    ALGORITHM: str = os.getenv("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30))
    REFRESH_TOKEN_EXPIRE_DAYS: int = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", 7))
    
    # CORS
    CORS_ORIGINS: List[str] = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")
    
    # App
    PROJECT_NAME: str = "Lanka Pass Travel API"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api"
    
    @property
    def is_production(self) -> bool:
        return os.getenv("ENVIRONMENT", "development") == "production"
    
    def validate(self):
        """Validate required environment variables"""
        required_vars = ["SUPABASE_URL", "SUPABASE_KEY", "SECRET_KEY"]
        for var in required_vars:
            if not getattr(self, var):
                raise ValueError(f"{var} environment variable is required")

settings = Settings()
settings.validate()