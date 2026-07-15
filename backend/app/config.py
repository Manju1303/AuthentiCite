import os
from pydantic_settings import BaseSettings
from pydantic import Field

class Settings(BaseSettings):
    PROJECT_NAME: str = "AuthentiCite - Academic Paper Rewriter & Similarity Analyzer"
    API_V1_STR: str = "/api/v1"
    
    # Database
    DATABASE_URL: str = Field(default="sqlite:///./research_ai.db", validation_alias="DATABASE_URL")
    
    # File Storage
    UPLOAD_DIR: str = Field(default="uploads", validation_alias="UPLOAD_DIR")
    OUTPUT_DIR: str = Field(default="output", validation_alias="OUTPUT_DIR")
    
    # LLM Settings
    LLM_PROVIDER: str = Field(default="gemini", validation_alias="LLM_PROVIDER") # gemini, ollama, deepseek
    OLLAMA_API_URL: str = Field(default="http://localhost:11434", validation_alias="OLLAMA_API_URL")
    OLLAMA_MODEL: str = Field(default="qwen2.5:7b", validation_alias="OLLAMA_MODEL")
    
    # Cloud API Keys
    GEMINI_API_KEY: str = Field(default="", validation_alias="GEMINI_API_KEY")
    DEEPSEEK_API_KEY: str = Field(default="", validation_alias="DEEPSEEK_API_KEY")
    
    # Similarity settings
    SIMILARITY_THRESHOLD: float = Field(default=0.20, validation_alias="SIMILARITY_THRESHOLD")
    EMBEDDING_MODEL: str = Field(default="all-MiniLM-L6-v2", validation_alias="EMBEDDING_MODEL")

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()

# Create directories if they do not exist
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
os.makedirs(settings.OUTPUT_DIR, exist_ok=True)
