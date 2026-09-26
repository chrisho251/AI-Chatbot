"""A complete platform that runs without Docker, for unit tests in any lane.

SQLite replaces Postgres, a temporary folder replaces the object store and an in memory index
replaces pgvector. Every other table, the ingest, eval and ft schemas included, is created on the
same SQLite file. Behaviour matches production except search scores. Use it from a pytest fixture
with tmp_path.
"""

from pathlib import Path

from chatbot_platform.factory import Platform
from chatbot_platform.index import InMemoryServingIndex
from chatbot_platform.registry import Registry
from chatbot_platform.settings import BUCKETS, PlatformSettings
from chatbot_platform.sql import sqlite_engine
from chatbot_platform.storage import LocalFsObjectStore


def make_test_platform(root: Path, embedding_dim: int = 8) -> Platform:
    root.mkdir(parents=True, exist_ok=True)
    settings = PlatformSettings(
        database_url=f"sqlite:///{(root / 'platform.db').as_posix()}",
        object_store="local",
        local_root=str(root / "objects"),
        embedding_dim=embedding_dim,
        _env_file=None,
    )
    engine = sqlite_engine(settings.database_url)
    registry = Registry(engine)
    registry.create_tables()
    store = LocalFsObjectStore(root / "objects")
    for bucket in BUCKETS:
        store.ensure_bucket(bucket)
    return Platform(
        settings=settings,
        engine=engine,
        store=store,
        index=InMemoryServingIndex(),
        registry=registry,
    )
