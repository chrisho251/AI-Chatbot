"""Apply Postgres migrations with Alembic. The platform CLI init command calls upgrade."""

from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import Connection

MIGRATIONS = Path(__file__).parent / "migrations"


def alembic_config(database_url: str, embedding_dim: int) -> Config:
    config = Config()
    config.set_main_option("script_location", str(MIGRATIONS))
    config.set_main_option("sqlalchemy.url", database_url.replace("%", "%%"))
    config.attributes["embedding_dim"] = embedding_dim
    return config


def upgrade(database_url: str, embedding_dim: int, connection: Connection | None = None) -> None:
    """Pass connection to run inside an existing connection, for example in tests."""
    config = alembic_config(database_url, embedding_dim)
    config.attributes["connection"] = connection
    command.upgrade(config, "head")
