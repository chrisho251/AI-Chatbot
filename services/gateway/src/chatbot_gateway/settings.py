"""Gateway settings, read from GATEWAY_ environment variables."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class GatewaySettings(BaseSettings):
    """Limits are placeholders until the Appendix D thresholds are agreed."""

    model_config = SettingsConfigDict(env_prefix="GATEWAY_", env_file=".env", extra="ignore")

    oidc_issuer: str = "http://keycloak:8080/realms/chatbot"
    oidc_audience: str = "chatbot"
    requests_per_minute: int = 20
    max_in_flight: int = 16
    max_upload_bytes: int = 10_000_000
    upload_media_types: tuple[str, ...] = ("image/jpeg", "image/png", "text/csv")
