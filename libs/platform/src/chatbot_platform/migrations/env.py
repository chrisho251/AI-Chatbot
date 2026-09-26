"""Alembic environment. Migrations run online against PLATFORM_DATABASE_URL.

Autogenerate compares every schema in sql.metadata, which is all of them except serving. Views,
and every change to the serving schema, are written by hand, the serving tables depend on the
embedding dimension.
"""

from alembic import context
from sqlalchemy import create_engine
from sqlalchemy.pool import NullPool

from chatbot_platform import sql
from chatbot_platform.settings import PlatformSettings


def _include_name(name, type_, _parent_names) -> bool:
    return type_ != "schema" or name in set(sql.SCHEMAS) - {sql.SERVING}


def _run(connection) -> None:
    context.configure(
        connection=connection,
        target_metadata=sql.metadata,
        include_schemas=True,
        include_name=_include_name,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations() -> None:
    shared = context.config.attributes.get("connection")
    if shared is not None:
        _run(shared)
        return
    url = context.config.get_main_option("sqlalchemy.url") or PlatformSettings().database_url
    with create_engine(url, poolclass=NullPool).connect() as connection:
        _run(connection)


run_migrations()
