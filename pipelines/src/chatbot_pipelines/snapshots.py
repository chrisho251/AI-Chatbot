"""Copy hot ops rows into the Iceberg history tables. Stub owned by Lane A.

Purpose
Online services write to ops tables in Postgres because it is fast. Reports, evaluation and the
lineage sweep read history from Iceberg, see ARCHITECTURE.md section 4.2.

What to build
For each pair of ops table and history table, read rows newer than the last copied timestamp and
append them with lake.append_rows. Keep the high water mark in a small registry table or a Dagster
cursor. Never copy the encrypted question text into history.

How to test
Insert ops rows with make_test_platform, copy twice, and assert no duplicates.
"""


def copy_new_rows() -> dict[str, int]:
    """Table name to the number of rows copied."""
    raise NotImplementedError("history snapshots are not written yet")
