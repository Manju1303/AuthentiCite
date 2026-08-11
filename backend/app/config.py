import os
from pydantic_settings import BaseSettings
from pydantic import Field, ConfigDict

class Settings(BaseSettings):
    PROJECT_NAME: str = "AuthentiCite - Academic Paper Rewriter & Similarity Analyzer"
    API_V1_STR: str = "/api/v1"
    
    # Database
    DATABASE_URL: str = Field(default="sqlite:///./research_ai.db", validation_alias="DATABASE_URL")
    
    # File Storage
    UPLOAD_DIR: str = Field(default="uploads", validation_alias="UPLOAD_DIR")
    OUTPUT_DIR: str = Field(default="output", validation_alias="OUTPUT_DIR")
    
    # LLM Settings (Supports 28B/32B parameter models & Claude 3.5/3.7 Sonnet)
    LLM_PROVIDER: str = Field(default="gemini", validation_alias="LLM_PROVIDER") # gemini, claude, ollama, deepseek
    OLLAMA_API_URL: str = Field(default="http://localhost:11434", validation_alias="OLLAMA_API_URL")
    OLLAMA_MODEL: str = Field(default="qwen2.5:32b", validation_alias="OLLAMA_MODEL")
    CLAUDE_MODEL: str = Field(default="claude-3-5-sonnet-20241022", validation_alias="CLAUDE_MODEL")
    GEMINI_MODEL: str = Field(default="gemini-2.5-flash", validation_alias="GEMINI_MODEL")
    DEEPSEEK_MODEL: str = Field(default="deepseek-chat", validation_alias="DEEPSEEK_MODEL")
    LLM_TEMPERATURE: float = Field(default=0.2, validation_alias="LLM_TEMPERATURE")
    MAX_TOKENS: int = Field(default=4096, validation_alias="MAX_TOKENS")
    
    # Cloud API Keys
    GEMINI_API_KEY: str = Field(default="", validation_alias="GEMINI_API_KEY")
    DEEPSEEK_API_KEY: str = Field(default="", validation_alias="DEEPSEEK_API_KEY")
    ANTHROPIC_API_KEY: str = Field(default="", validation_alias="ANTHROPIC_API_KEY")
    SEMANTIC_SCHOLAR_API_KEY: str = Field(default="", validation_alias="SEMANTIC_SCHOLAR_API_KEY")
    
    # Similarity settings
    SIMILARITY_THRESHOLD: float = Field(default=0.20, validation_alias="SIMILARITY_THRESHOLD")
    EMBEDDING_MODEL: str = Field(default="all-MiniLM-L6-v2", validation_alias="EMBEDDING_MODEL")

    # CopyLeaks API Keys
    COPYLEAKS_EMAIL: str = Field(default="", validation_alias="COPYLEAKS_EMAIL")
    COPYLEAKS_API_KEY: str = Field(default="", validation_alias="COPYLEAKS_API_KEY")
    
    # Feature Toggles
    USE_COPYLEAKS: bool = Field(default=False, validation_alias="USE_COPYLEAKS")
    USE_CREWAI: bool = Field(default=False, validation_alias="USE_CREWAI")
    USE_MARKER: bool = Field(default=False, validation_alias="USE_MARKER")
    
    # RAG & OCR Settings
    QDRANT_URL: str = Field(default="", validation_alias="QDRANT_URL")
    QDRANT_API_KEY: str = Field(default="", validation_alias="QDRANT_API_KEY")
    RAG_RERANKER_MODEL: str = Field(default="ms-marco-MiniLM-L-6-v2", validation_alias="RAG_RERANKER_MODEL")
    NEMOTRON_API_KEY: str = Field(default="", validation_alias="NEMOTRON_API_KEY")
    GEMMA_OCR_ENDPOINT: str = Field(default="", validation_alias="GEMMA_OCR_ENDPOINT")

    model_config = ConfigDict(env_file=".env", extra="ignore")

settings = Settings()

# Create directories if they do not exist
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
os.makedirs(settings.OUTPUT_DIR, exist_ok=True)
