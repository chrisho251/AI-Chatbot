"""Build the platform from settings. This is the only place that chooses adapters."""

from dataclasses import dataclass
from pathlib import Path

from sqlalchemy import Engine, create_engine

from chatbot_platform.index import ServingIndex
from chatbot_platform.pg_index import PgServingIndex
from chatbot_platform.registry import Registry
from chatbot_platform.settings import PlatformSettings
from chatbot_platform.storage import LocalFsObjectStore, ObjectStore, S3ObjectStore


@dataclass
class Platform:
    settings: PlatformSettings
    engine: Engine
    store: ObjectStore
    index: ServingIndex
    registry: Registry


def build_store(settings: PlatformSettings) -> ObjectStore:
    if settings.object_store == "local":
        return LocalFsObjectStore(Path(settings.local_root))
    return S3ObjectStore(
        endpoint_url=settings.s3_endpoint_url,
        access_key=settings.s3_access_key,
        secret_key=settings.s3_secret_key.get_secret_value(),
        region=settings.s3_region,
    )


def build_platform(settings: PlatformSettings | None = None) -> Platform:
    settings = settings or PlatformSettings()
    engine = create_engine(settings.database_url, pool_pre_ping=True)
    return Platform(
        settings=settings,
        engine=engine,
        store=build_store(settings),
        index=PgServingIndex(engine, settings.embedding_dim),
        registry=Registry(engine),
    )
