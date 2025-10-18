# /core/config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str
    UPLOAD_DIRECTORY: str

    class Config:
        env_file = ".env"

settings = Settings()
