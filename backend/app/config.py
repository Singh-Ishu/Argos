from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent

class Settings(BaseSettings):
    API_NINJAS_KEY: str 
    EIA_API_KEY: str = ""
    ACLED_EMAIL: str = ""
    ACLED_PASSWORD: str = ""

    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env", 
        env_file_encoding="utf-8"
    )

settings = Settings()