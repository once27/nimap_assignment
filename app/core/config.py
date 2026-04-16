from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    DATABASE_URL: str
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    
    QDRANT_HOST: str = "localhost"
    QDRANT_PORT: int = 6333
    
    # RAG Settings
    CHUNK_SIZE: int = 512
    CHUNK_OVERLAP: int = 50

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
