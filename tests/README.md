# Cross-package tests

Unit tests live next to their package, in `<package>/tests`. This folder holds tests that span packages.

- `tooling/`: tests for the scripts in `scripts/` (comment rule, lane boundaries). Run with `uv run pytest tests/tooling`.
- `load/`: the Locust load test for the 10 concurrent user target. Run it with `uvx locust -f tests/load/locustfile.py --host https://localhost --users 10` against a running stack, with `LOAD_TEST_TOKEN` set to a test student token. Lane D owns it.
- `integration/` (to add): tests that start the `data` profile and more, marked `integration`.
- `e2e/` (to add at M5): a question sent to the gateway in a running stack comes back as a cited answer, an external-source answer, or an expert escalation. Lane C owns it, with Lane D for the Appendix C levels.
