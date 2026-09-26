"""Settings shared by every service, read from CHATBOT_ environment variables."""

import os

from pydantic_settings import BaseSettings, SettingsConfigDict


class ServiceSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="CHATBOT_", env_file=".env", extra="ignore")

    environment: str = "local"
    log_level: str = "INFO"
    llm_base_url: str = "http://localhost:8080/v1"
    llm_model: str = "qwen3-4b-instruct"
    embed_base_url: str = "http://localhost:8081"
    rerank_base_url: str = "http://localhost:8082"
    request_timeout_s: float = 60.0
    key_file: str = "infra/local/keys/keys.json"
    otel_endpoint: str = ""


def service_url(service: str) -> str:
    """Base url of a component that runs in its own container.

    Only used for endpoints without a local handler. Set CHATBOT_<SERVICE>_URL to point at it,
    otherwise the compose host name of the service is used.
    """
    override = os.environ.get(f"CHATBOT_{service.upper()}_URL")
    return override or f"http://{service.replace('_', '-')}:8000"
