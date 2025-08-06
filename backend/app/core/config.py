from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # OpenAI Configuration
    openai_api_key: str = ""

    # Pinecone Configuration
    pinecone_api_key: str = ""
    pinecone_environment: str = ""
    pinecone_index_name: str = "docuverse"

    # MongoDB Configuration
    mongodb_uri: str = "mongodb://localhost:27017/docuverse"

    # Redis Configuration (for Celery)
    redis_url: str = "redis://localhost:6379/0"

    # Celery Configuration
    celery_broker_url: str = "redis://localhost:6379/0"
    celery_result_backend: str = "redis://localhost:6379/0"

    # Backend Configuration
    backend_url: str = "http://localhost:8000"

    # File Upload Configuration
    upload_dir: str = "uploads"
    max_file_size: int = 50 * 1024 * 1024  # 50MB

    # Supported file types
    supported_extensions: list[str] = [".pdf", ".docx", ".csv", ".xlsx", ".xls", ".png", ".jpg", ".jpeg"]

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
