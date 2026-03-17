from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    # App config
    api_v1_prefix: str = "/api/v1"
    
    # Auth
    secret_key: str = "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 1440 # 1 day
    
    # ERPNext Configuration
    erpnext_url: Optional[str] = None
    erpnext_api_key: Optional[str] = None
    erpnext_api_secret: Optional[str] = None
    erpnext_site_name: Optional[str] = None

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
