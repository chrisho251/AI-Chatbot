"""Schedules of the offline plane. Stub owned by Lane A, with the eval lane for RAGAs.

What to build
Hourly, copy new ops rows into the Iceberg history tables with snapshots.copy_new_rows, and snapshot
Prometheus metrics into obs tables.
Daily, run retention.run_retention and lineage.sweep_superseded, then open SME tickets.
Nightly, RAGAs on the golden set and on sampled live traffic, off peak.
Weekly, W7 enrichment for every course topic.

How to test
Assert the cron strings and that each schedule targets the right job.
"""
