# AI-chatbot

Backend of a AI chatbot. It uses open-weight models only, RAG with eight workers, RAGAs evaluation, and escalation to external sources and human experts. It runs locally first and moves to AWS later.

**Read next:**
- [docs/architecture/ARCHITECTURE.md](docs/architecture/ARCHITECTURE.md): how the system works.
- [docs/TECH_STACK.md](docs/TECH_STACK.md): every tool, service and model, what your machine needs, and what costs money (section 11).
- [docs/MONITORING.md](docs/MONITORING.md): metrics, dashboards, and the milestone performance summary.

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
- `libs/platform`: the data platform. It is implemented and tested.
- `libs/common`: FastAPI app factory, contract client, test fakes, LLM and embedding clients.
- `services/`: gateway, orchestrator, escalation.
- `workers/`: W1 to W8, one package and one image each.
- `pipelines/`: Dagster code location for the offline plane.
- `ml/`: evaluation and fine-tuning.
- `infra/`: Dockerfile, local configuration, AWS (phase 2).
- `scripts/`: comment rule check, lane boundary check, dashboard check, CI package selection, test runner.
- `docs/`: architecture, tech stack, diagrams.

## Useful tasks

- `uv run poe lint`: ruff lint.
- `uv run poe format`: ruff format.
- `uv run poe check-comments`: the comment rule.
- `uv run poe check-boundaries`: lane boundaries.
- `uv run poe check-dashboards`: dashboards match the metric catalogue and the reporting schema.
- `uv run poe test`: every package.
- `uv run poe up-data`: start Postgres and SeaweedFS.
- `uv run poe init-platform`: migrate the database, create buckets and lake tables.
- `uv run poe export-schemas`: regenerate `libs/contracts/schemas` after a contract change.
- `uv run poe down`: stop every container.

Install the git hooks once with `uv run pre-commit install`.
