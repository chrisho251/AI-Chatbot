"""Orchestrator settings, read from ORCHESTRATOR_ environment variables."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class OrchestratorSettings(BaseSettings):
    """Thresholds are placeholders to tune on SME labelled answers."""

    model_config = SettingsConfigDict(env_prefix="ORCHESTRATOR_", env_file=".env", extra="ignore")

    l1_threshold: float = 0.75
    l2_threshold: float = 0.50
    sufficiency_floor: float = 0.20
    retrieve_k: int = 8
    model_version: str = "qwen3-4b-instruct"
    prompt_version: str = "answer-v1"
