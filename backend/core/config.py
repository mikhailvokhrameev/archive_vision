from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Database URL
    DATABASE_URL: str
    
    # Directory settings
    DATA_DIRECTORY: str = "data"
    UPLOADS_DIRECTORY: str = "data/uploads"
    TRANSCRIPTS_DIRECTORY: str = "data/transcripts"
    CORRECTIONS_DIRECTORY: str = "data/corrections"
    
    class Config:
        env_file = ".env"
        extra = "allow"  # ← Измените "ignore" на "allow" чтобы игнорировать лишние поля

settings = Settings()