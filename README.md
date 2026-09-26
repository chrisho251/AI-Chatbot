# AI-chatbot

Backend of an AI chatbot. It uses open-weight models only, RAG with eight workers, RAGAs evaluation, and escalation to external sources and human experts. The whole online plane runs as one `api` service, and Postgres is the only database. It runs locally first and moves to AWS later.

**Read next:**
- [docs/architecture/ARCHITECTURE.md](docs/architecture/ARCHITECTURE.md): how the system works.
- [docs/TECH_STACK.md](docs/TECH_STACK.md): every tool, service and model, what your machine needs, and what costs money (section 11).
- [docs/MONITORING.md](docs/MONITORING.md): metrics, dashboards, and the milestone performance summary.
- [docs/CHANGELOG.md](docs/CHANGELOG.md): what changed in each version of the design.

---

## Quick start

You need Docker (with Compose v2), Git and [uv](https://docs.astral.sh/uv/). uv installs Python 3.12 by itself.

```bash
cp .env.example .env
uv sync
uv run poe test
```

`uv run poe test` runs every package in its own environment. The first run downloads large libraries such as torch. To test only what you work on:

```bash
python scripts/run_tests.py chatbot-platform chatbot-w6-embed
```

To work with the real data platform (Postgres with pgvector, and SeaweedFS):

```bash
uv run poe up-data
uv run poe init-platform
uv run --package chatbot-platform chatbot-platform status
```

## Repository layout

- `libs/contracts`: typed records, HTTP routes and samples shared by every lane. Change them with care, see its README.
- `libs/platform`: the data platform on Postgres and an object store. It is implemented and tested.
- `libs/common`: FastAPI app factory, contract client, test fakes, LLM and embedding clients.
- `services/`: gateway, orchestrator, escalation, and `api`, which runs all of them and the online workers in one process.
- `workers/`: W1 to W8, one package each. Online roles run inside the api service, offline jobs run from the same image.
- `pipelines/`: Dagster code location for the offline plane.
- `ml/`: evaluation and fine-tuning.
- `infra/`: Dockerfile, local configuration, AWS (phase 2).
- `scripts/`: comment rule check, lane boundary check, dashboard check, CI package selection, test runner.
- `tests/`: cross-package tests and the Locust load test.
- `docs/`: architecture, tech stack, diagrams.

## Useful tasks

- `uv run poe lint`: ruff lint.
- `uv run poe format`: ruff format.
- `uv run poe check-comments`: the comment rule.
- `uv run poe check-boundaries`: lane boundaries.
- `uv run poe check-dashboards`: dashboards match the metric catalogue and the reporting schema.
- `uv run poe test`: every package.
- `uv run poe up-data`: start Postgres and SeaweedFS.
- `uv run poe init-platform`: migrate the database and create the buckets.
- `uv run poe export-schemas`: regenerate `libs/contracts/schemas` after a contract change.
- `uv run poe down`: stop every container.

Install the git hooks once with `uv run pre-commit install`.
