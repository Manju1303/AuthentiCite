import os

try:
    from pydantic_settings import BaseSettings
    from pydantic import Field, ConfigDict
except ImportError:
    try:
        from pydantic import BaseModel as BaseSettings, Field
        ConfigDict = dict
    except ImportError:
        class BaseSettings:
            pass
        def Field(default=None, **kwargs):
            return default
        ConfigDict = dict

class Settings(BaseSettings):
    PROJECT_NAME: str = "AuthentiCite - Academic Paper Rewriter & Similarity Analyzer"
    API_V1_STR: str = "/api/v1"
    
    # Database
    DATABASE_URL: str = Field(default="sqlite:///./research_ai.db")
    
    # File Storage
    UPLOAD_DIR: str = Field(default="uploads")
    OUTPUT_DIR: str = Field(default="output")
    
    # LLM Settings
    LLM_PROVIDER: str = Field(default="gemini")
    OLLAMA_API_URL: str = Field(default="http://localhost:11434")
    OLLAMA_MODEL: str = Field(default="qwen2.5:32b")
    CLAUDE_MODEL: str = Field(default="claude-3-5-sonnet-20241022")
    GEMINI_MODEL: str = Field(default="gemini-2.5-flash")
    DEEPSEEK_MODEL: str = Field(default="deepseek-chat")
    LLM_TEMPERATURE: float = Field(default=0.2)
    MAX_TOKENS: int = Field(default=4096)
    
    # Cloud API Keys
    GEMINI_API_KEY: str = Field(default="")
    DEEPSEEK_API_KEY: str = Field(default="")
    ANTHROPIC_API_KEY: str = Field(default="")
    SEMANTIC_SCHOLAR_API_KEY: str = Field(default="")
    
    # Similarity settings
    SIMILARITY_THRESHOLD: float = Field(default=0.20)
    EMBEDDING_MODEL: str = Field(default="all-MiniLM-L6-v2")

    # CopyLeaks API Keys
    COPYLEAKS_EMAIL: str = Field(default="")
    COPYLEAKS_API_KEY: str = Field(default="")
    
    # Feature Toggles
    USE_COPYLEAKS: bool = Field(default=False)
    USE_CREWAI: bool = Field(default=False)
    USE_MARKER: bool = Field(default=False)
    
    # RAG & OCR Settings
    QDRANT_URL: str = Field(default="")
    QDRANT_API_KEY: str = Field(default="")
    RAG_RERANKER_MODEL: str = Field(default="ms-marco-MiniLM-L-6-v2")
    NEMOTRON_API_KEY: str = Field(default="")
    GEMMA_OCR_ENDPOINT: str = Field(default="")

    try:
        model_config = ConfigDict(env_file=".env", extra="ignore")
    except Exception:
        pass

settings = Settings()

os.makedirs(getattr(settings, "UPLOAD_DIR", "uploads"), exist_ok=True)
os.makedirs(getattr(settings, "OUTPUT_DIR", "output"), exist_ok=True)
