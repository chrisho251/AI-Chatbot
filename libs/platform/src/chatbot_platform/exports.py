"""Write once Parquet files in the exports bucket.

A frozen dataset, such as a fine tuning dataset version or the items of an evaluation run, is
written here once as Parquet. The key holds the sha256 of the file, so an export is never
overwritten and its uri proves its content. pandas, DuckDB or Athena on AWS read the files as they
are, so analysis never needs a copy of the live database.
"""

import io
from collections.abc import Iterable
from dataclasses import dataclass
from typing import Any

import pyarrow as pa
import pyarrow.parquet as pq

from chatbot_contracts.ids import sha256_hex
from chatbot_platform.settings import EXPORTS_BUCKET
from chatbot_platform.storage import ObjectStore, object_uri, split_uri


@dataclass(frozen=True)
class Export:
    uri: str
    sha256: str
    rows: int


def export_rows(
    store: ObjectStore, name: str, rows: Iterable[dict[str, Any]], schema: pa.Schema | None = None
) -> Export:
    """Write the rows under name and return where they are. Writing the same file twice is safe."""
    table = pa.Table.from_pylist(list(rows), schema=schema)
    buffer = io.BytesIO()
    pq.write_table(table, buffer)
    data = buffer.getvalue()
    digest = sha256_hex(data)
    key = f"{name}/{digest}.parquet"
    if not store.exists(EXPORTS_BUCKET, key):
        store.put(EXPORTS_BUCKET, key, data)
    return Export(uri=object_uri(EXPORTS_BUCKET, key), sha256=digest, rows=table.num_rows)


def read_export(store: ObjectStore, uri: str) -> list[dict[str, Any]]:
    bucket, key = split_uri(uri)
    return pq.read_table(io.BytesIO(store.get(bucket, key))).to_pylist()
