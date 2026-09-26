"""Platform configuration, read from environment variables with the PLATFORM_ prefix."""

from typing import Literal

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

RAW_BUCKET = "raw"
UPLOADS_BUCKET = "uploads"
EXTERNAL_BUCKET = "external"
EXPORTS_BUCKET = "exports"
MLFLOW_BUCKET = "mlflow"
BUCKETS = (RAW_BUCKET, UPLOADS_BUCKET, EXTERNAL_BUCKET, EXPORTS_BUCKET, MLFLOW_BUCKET)


class PlatformSettings(BaseSettings):
    """Defaults match the data profile of compose.yaml on localhost.

    Retention days and gate thresholds are placeholders until the Institution agrees on values.
    """

    model_config = SettingsConfigDict(env_prefix="PLATFORM_", env_file=".env", extra="ignore")

    database_url: str = "postgresql+psycopg://chatbot:chatbot@localhost:5432/chatbot"

    object_store: Literal["local", "s3"] = "s3"
    local_root: str = "data/objects"
    s3_endpoint_url: str | None = "http://localhost:8333"
    s3_access_key: str = "chatbot"
    s3_secret_key: SecretStr = SecretStr("chatbot-secret")
    s3_region: str = "us-east-1"

    embedding_dim: int = 1024

    gate_min_ocr_confidence: float = 0.80
    gate_max_duplicate_rate: float = 0.05

    retention_uploads_days: int = 30
    retention_text_days: int = 365
    retention_ops_days: int = 730
    retention_staging_days: int = 90
