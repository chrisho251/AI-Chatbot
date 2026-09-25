"""Analytics queries over the lake. Stub owned by Lane D, needed for reports and dashboards.

Purpose
Run SQL over Iceberg history tables for the monitoring dashboard, the milestone performance summary
and the Appendix C test documentation. DuckDB locally, Athena on AWS.

What to build
A QueryEngine protocol with one method, query, that takes SQL and returns a pyarrow Table.
DuckDbQueryEngine reads tables through lake.read_rows or the DuckDB iceberg extension.
AthenaQueryEngine is phase 2 and belongs next to it.
Keep queries in one place, for example a reports module in ml eval, so both engines share them.

How to test
Write rows with lake.append_rows into a catalog from testing.make_test_platform, then query them.
"""

from typing import Protocol

import pyarrow as pa


class QueryEngine(Protocol):
    def query(self, sql: str) -> pa.Table: ...
