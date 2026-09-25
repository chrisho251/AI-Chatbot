"""A complete platform that runs without Docker, for unit tests in any lane.

SQLite replaces Postgres, a temporary folder replaces the object store, an in memory index replaces
pgvector and a SQLite Iceberg catalog replaces the Postgres one. Behaviour matches production
except search scores. Use it from a pytest fixture with tmp_path.
"""

from pathlib import Path

from pyiceberg.catalog.sql import SqlCatalog

from chatbot_platform.factory import Platform
from chatbot_platform.index import InMemoryServingIndex
from chatbot_platform.lake import ensure_tables
from chatbot_platform.registry import Registry
from chatbot_platform.settings import BUCKETS, PlatformSettings
from chatbot_platform.sql import sqlite_engine
from chatbot_platform.storage import LocalFsObjectStore


def make_test_platform(root: Path, embedding_dim: int = 8, with_lake: bool = True) -> Platform:
    root.mkdir(parents=True, exist_ok=True)
    settings = PlatformSettings(
        database_url=f"sqlite:///{(root / 'platform.db').as_posix()}",
        object_store="local",
        local_root=str(root / "objects"),
        warehouse=str(root / "warehouse"),
        embedding_dim=embedding_dim,
        _env_file=None,
    )
    engine = sqlite_engine(settings.database_url)
    registry = Registry(engine)
    registry.create_tables()
    store = LocalFsObjectStore(root / "objects")
    for bucket in BUCKETS:
        store.ensure_bucket(bucket)
    catalog = None
    if with_lake:
        (root / "warehouse").mkdir(exist_ok=True)
        catalog = SqlCatalog(
            "test",
            uri=f"sqlite:///{(root / 'catalog.db').as_posix()}",
            warehouse=settings.warehouse,
        )
        ensure_tables(catalog)
    return Platform(
        settings=settings,
        engine=engine,
        store=store,
        index=InMemoryServingIndex(),
        registry=registry,
        _catalog=catalog,
    )
