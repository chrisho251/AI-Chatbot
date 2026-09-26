"""Schedules of the offline plane. Stub owned by Lane A, with the eval lane for RAGAs.

What to build
Daily, run retention.run_retention and lineage.sweep_superseded, then open SME tickets.
Nightly, RAGAs on the golden set and on sampled live traffic, off peak.
Weekly, W7 enrichment for every course topic.
There is no copy job. Operational rows stay in the ops tables for their whole life, and Prometheus
keeps 90 days of metrics.

How to test
Assert the cron strings and that each schedule targets the right job.
"""
