from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # MongoDB Configuration
    mongodb_uri: str
    mongodb_dbname: str

    # Qdrant Configuration (replaces ChromaDB)
    qdrant_url: str                           # e.g. "https://<cluster-id>.<region>.gcp.cloud.qdrant.io"
    qdrant_api_key: str
    qdrant_collection_name: str = "documents"
    embedding_dim: int = 1536                  # Dimension for "text-embedding-3-small"

    # OpenAI Configuration
    openai_api_key: str
    openai_chat_model: str = "gpt-4o-mini"
    embedding_model: str = "text-embedding-3-small"

    # JWT Configuration
    jwt_secret: str
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    # RAG Configuration
    retrieval_top_k: int = 5
    retrieval_score_min: float = 0.7

    # Server Configuration
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = True

    class Config:
        env_file = ".env"
        case_sensitive = False

settings = Settings()
