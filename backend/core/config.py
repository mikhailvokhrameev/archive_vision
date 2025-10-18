# /core/config.py
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str
    DATA_DIRECTORY: str = "data"
    UPLOADS_DIRECTORY: str = "data/uploads"
    TRANSCRIPTS_DIRECTORY: str = "data/transcripts"
    CORRECTIONS_DIRECTORY: str = "data/corrections"


    class Config:
        env_file = ".env"
        extra = "ignore"  # This will ignore any fields not defined in the model


settings = Settings()