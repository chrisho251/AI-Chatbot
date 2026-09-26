"""SQL tables of the chatbot database. Postgres is the only database of the platform.

metadata holds the registry, ops, ingest, eval, ft and reporting schemas. They only use portable
types, so unit tests can run them on SQLite. The serving schema needs pgvector and full text search,
so it only exists on Postgres and is built by serving_tables.
Operational tables are both the hot data and the history. Retention blanks free text and deletes old
rows in place, see retention.py.
"""

from dataclasses import dataclass
from datetime import UTC, datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    Computed,
    DateTime,
    Engine,
    Float,
    ForeignKey,
    Index,
    Integer,
    MetaData,
    String,
    Table,
    Text,
    create_engine,
    event,
)
from sqlalchemy.dialects.postgresql import JSONB, TSVECTOR
from sqlalchemy.pool import StaticPool

REGISTRY = "registry"
SERVING = "serving"
OPS = "ops"
INGEST = "ingest"
EVAL = "eval"
FT = "ft"
REPORTING = "reporting"
SCHEMAS = (REGISTRY, SERVING, OPS, INGEST, EVAL, FT, REPORTING)


def utcnow() -> datetime:
    return datetime.now(UTC)


def as_utc(value: datetime | None) -> datetime | None:
    """SQLite drops the timezone, so treat naive values as UTC."""
    if value is None or value.tzinfo is not None:
        return value
    return value.replace(tzinfo=UTC)


def _json() -> JSON:
    return JSON().with_variant(JSONB(), "postgresql")


def _ts() -> DateTime:
    return DateTime(timezone=True)


metadata = MetaData()

doc_versions = Table(
    "doc_versions",
    metadata,
    Column("doc_version", String, primary_key=True),
    Column("doc_id", String, nullable=False, index=True),
    Column("sha256", String(64), nullable=False),
    Column("source_type", String, nullable=False),
    Column("course_code", String, nullable=False),
    Column("source_id", String, nullable=False),
    Column("raw_uri", String, nullable=False),
    Column("licence", String),
    Column("source_url", String),
    Column("page_count", Integer),
    Column("supersedes", String, index=True),
    Column("retracted_at", _ts()),
    Column("producer", String, nullable=False),
    Column("created_at", _ts(), nullable=False),
    schema=REGISTRY,
)

ingestion_runs = Table(
    "ingestion_runs",
    metadata,
    Column("run_id", String, primary_key=True),
    Column("doc_version", String, ForeignKey(doc_versions.c.doc_version), nullable=False),
    Column("dagster_run_id", String),
    Column("status", String, nullable=False),
    Column("started_at", _ts(), nullable=False),
    Column("finished_at", _ts()),
    Column("worker_digests", _json(), nullable=False, default=dict),
    Column("model_versions", _json(), nullable=False, default=dict),
    schema=REGISTRY,
)

kb_versions = Table(
    "kb_versions",
    metadata,
    Column("version_id", Integer, primary_key=True, autoincrement=False),
    Column("parent_version", Integer),
    Column("doc_versions", _json(), nullable=False),
    Column("embedding_model", String, nullable=False),
    Column("chunker_version", String, nullable=False),
    Column("status", String, nullable=False),
    Column("gate_report_id", String),
    Column("created_at", _ts(), nullable=False),
    Column("published_at", _ts()),
    schema=REGISTRY,
)

kb_aliases = Table(
    "kb_aliases",
    metadata,
    Column("name", String, primary_key=True),
    Column("version_id", Integer, nullable=False),
    Column("updated_at", _ts(), nullable=False),
    schema=REGISTRY,
)

gate_reports = Table(
    "gate_reports",
    metadata,
    Column("report_id", String, primary_key=True),
    Column("version_id", Integer, nullable=False, index=True),
    Column("checks", _json(), nullable=False),
    Column("requires_sme", Boolean, nullable=False),
    Column("sme_decision", String),
    Column("sme_by", String),
    Column("sme_comment", Text),
    Column("sme_at", _ts()),
    Column("created_at", _ts(), nullable=False),
    schema=REGISTRY,
)

interactions = Table(
    "interactions",
    metadata,
    Column("request_id", String, primary_key=True),
    Column("pseudo_user", String, nullable=False, index=True),
    Column("conversation_id", String, index=True),
    Column("question_enc", Text, nullable=False),
    Column("answer", Text),
    Column("kb_version", Integer),
    Column("model_version", String),
    Column("prompt_version", String),
    Column("confidence", Float),
    Column("level", String),
    Column("used_external", Boolean, nullable=False, default=False),
    Column("escalated", Boolean, nullable=False, default=False),
    Column("source_corrected", Boolean, nullable=False, default=False),
    Column("created_at", _ts(), nullable=False, index=True),
    schema=OPS,
)

citations = Table(
    "citations",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("request_id", String, ForeignKey(interactions.c.request_id), nullable=False),
    Column("chunk_id", String, index=True),
    Column("url", String),
    Column("doc_version", String),
    Column("page", Integer),
    schema=OPS,
)

tool_calls = Table(
    "tool_calls",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("request_id", String, ForeignKey(interactions.c.request_id), nullable=False),
    Column("tool", String, nullable=False),
    Column("operation", String, nullable=False),
    Column("language", String),
    Column("verdict", String, nullable=False),
    Column("duration_ms", Float, nullable=False),
    Column("error", Text),
    Column("created_at", _ts(), nullable=False),
    schema=OPS,
)

escalation_tickets = Table(
    "escalation_tickets",
    metadata,
    Column("ticket_id", String, primary_key=True),
    Column("request_id", String, nullable=False, index=True),
    Column("pseudo_user", String, nullable=False),
    Column("question_enc", Text, nullable=False),
    Column("confidence", Float, nullable=False),
    Column("status", String, nullable=False),
    Column("context_ids", _json(), nullable=False, default=list),
    Column("external_results", _json(), nullable=False, default=list),
    Column("external_response_ms", Float),
    Column("expert", String),
    Column("answer", Text),
    Column("created_at", _ts(), nullable=False, index=True),
    Column("answered_at", _ts()),
    schema=OPS,
)

expert_rota = Table(
    "expert_rota",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("expert", String, nullable=False),
    Column("contact", String, nullable=False),
    Column("starts_at", _ts(), nullable=False),
    Column("ends_at", _ts(), nullable=False),
    schema=OPS,
)

external_candidates = Table(
    "external_candidates",
    metadata,
    Column("candidate_id", String, primary_key=True),
    Column("url", String, nullable=False),
    Column("snapshot_sha256", String(64), nullable=False),
    Column("found_by", String, nullable=False),
    Column("status", String, nullable=False),
    Column("licence", String),
    Column("course_code", String),
    Column("topic", String),
    Column("decided_by", String),
    Column("decided_at", _ts()),
    Column("created_at", _ts(), nullable=False),
    schema=OPS,
)

uploads = Table(
    "uploads",
    metadata,
    Column("attachment_id", String, primary_key=True),
    Column("request_id", String, nullable=False, index=True),
    Column("media_type", String, nullable=False),
    Column("uri", String, nullable=False),
    Column("sha256", String(64), nullable=False),
    Column("size_bytes", Integer, nullable=False),
    Column("created_at", _ts(), nullable=False, index=True),
    schema=OPS,
)


conversations = Table(
    "conversations",
    metadata,
    Column("conversation_id", String, primary_key=True),
    Column("pseudo_user", String, nullable=False, index=True),
    Column("started_at", _ts(), nullable=False),
    Column("last_active_at", _ts(), nullable=False, index=True),
    schema=OPS,
)

request_facts = Table(
    "request_facts",
    metadata,
    Column("request_id", String, primary_key=True),
    Column("level", String, nullable=False),
    Column("latency_ms", Float),
    Column("e2e_ms", Float),
    Column("tokens_in", Integer),
    Column("tokens_out", Integer),
    Column("guard_verdict", String),
    Column("attachment_count", Integer, nullable=False, default=0),
    Column("created_at", _ts(), nullable=False, index=True),
    schema=OPS,
)
"""One row per request, written by the gateway. Blocked requests are included."""

guard_events = Table(
    "guard_events",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("request_id", String, index=True),
    Column("detector", String, nullable=False),
    Column("stage", String, nullable=False),
    Column("category", String, nullable=False),
    Column("score", Float, nullable=False),
    Column("action", String, nullable=False),
    Column("created_at", _ts(), nullable=False, index=True),
    schema=OPS,
)


def _record_columns() -> list[Column]:
    """Columns every ingest row carries, so the contract record can be rebuilt from the row."""
    return [
        Column("ingestion_run_id", String, primary_key=True),
        Column("schema_version", String, nullable=False),
        Column("producer", String, nullable=False),
        Column("created_at", _ts(), nullable=False, index=True),
    ]


regions = Table(
    "regions",
    metadata,
    *_record_columns(),
    Column("region_id", String, primary_key=True),
    Column("doc_version", String, nullable=False, index=True),
    Column("page_no", Integer, nullable=False),
    Column("kind", String, nullable=False),
    Column("bbox", _json()),
    Column("raw_text", Text),
    Column("image_uri", String),
    schema=INGEST,
)

extracted_regions = Table(
    "extracted_regions",
    metadata,
    *_record_columns(),
    Column("region_id", String, primary_key=True),
    Column("kind", String, nullable=False),
    Column("content", Text, nullable=False),
    Column("extractor", _json(), nullable=False),
    Column("confidence", Float, nullable=False),
    schema=INGEST,
)

cleaned_pages = Table(
    "cleaned_pages",
    metadata,
    *_record_columns(),
    Column("doc_version", String, primary_key=True),
    Column("page_no", Integer, primary_key=True),
    Column("markdown", Text, nullable=False),
    Column("region_ids", _json(), nullable=False),
    Column("flags", _json(), nullable=False),
    schema=INGEST,
)
"""The cleaned tier. It is kept, so a new embedding model rebuilds from here without new OCR."""

staged_chunks = Table(
    "chunks",
    metadata,
    *_record_columns(),
    Column("chunk_id", String, primary_key=True),
    Column("doc_version", String, nullable=False, index=True),
    Column("embedding_model", String, nullable=False),
    Column("chunker_version", String, nullable=False),
    Column("page_start", Integer, nullable=False),
    Column("page_end", Integer, nullable=False),
    Column("section_path", _json(), nullable=False),
    Column("text", Text, nullable=False),
    Column("kinds", _json(), nullable=False),
    Column("token_count", Integer, nullable=False),
    Column("region_ids", _json(), nullable=False),
    Column("embedding", _json(), nullable=False),
    schema=INGEST,
)
"""The chunked tier. Chunk sets wait here for the gate, publish copies them into serving.chunks and
retention deletes old staged rows."""

ragas_scores = Table(
    "ragas_scores",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("run_id", String, nullable=False, index=True),
    Column("kb_version", Integer),
    Column("model_version", String),
    Column("prompt_version", String),
    Column("dataset", String, nullable=False),
    Column("item_id", String, nullable=False),
    Column("metric", String, nullable=False),
    Column("score", Float, nullable=False),
    Column("judge_model", String),
    Column("created_at", _ts(), nullable=False),
    schema=EVAL,
)

test_cases = Table(
    "test_cases",
    metadata,
    Column("case_id", String, primary_key=True),
    Column("level", Integer, nullable=False),
    Column("question", Text, nullable=False),
    Column("source", String),
    Column("reference_answer", Text),
    Column("course_code", String),
    Column("topic", String),
    Column("created_at", _ts(), nullable=False),
    schema=EVAL,
)

test_runs = Table(
    "test_runs",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("run_id", String, nullable=False, index=True),
    Column("case_id", String, ForeignKey(test_cases.c.case_id), nullable=False),
    Column("response", Text),
    Column("level_reached", String),
    Column("confidence", Float),
    Column("escalated", Boolean, nullable=False, default=False),
    Column("ragas", _json(), nullable=False, default=dict),
    Column("remediation", Text),
    Column("created_at", _ts(), nullable=False),
    schema=EVAL,
)

ft_datasets = Table(
    "datasets",
    metadata,
    Column("dataset_version", String, primary_key=True),
    Column("item_count", Integer, nullable=False),
    Column("manifest_sha256", String(64), nullable=False),
    Column("export_uri", String, nullable=False),
    Column("status", String, nullable=False),
    Column("approved_by", String),
    Column("approved_at", _ts()),
    Column("comment", Text),
    Column("created_at", _ts(), nullable=False),
    schema=FT,
)
"""A frozen fine tuning dataset. Its items are also written once as Parquet to export_uri."""

ft_items = Table(
    "items",
    metadata,
    Column("dataset_version", String, ForeignKey(ft_datasets.c.dataset_version), primary_key=True),
    Column("item_id", String, primary_key=True),
    Column("split", String, nullable=False),
    Column("course_code", String),
    Column("topic", String),
    Column("question", Text, nullable=False),
    Column("answer", Text, nullable=False),
    Column("source", String, nullable=False),
    schema=FT,
)


ragas_summary = Table(
    "ragas_summary",
    metadata,
    Column("run_id", String, primary_key=True),
    Column("metric", String, primary_key=True),
    Column("ts", _ts(), nullable=False),
    Column("dataset", String, nullable=False),
    Column("kb_version", Integer),
    Column("model_version", String),
    Column("prompt_version", String),
    Column("judge_model", String),
    Column("mean_score", Float, nullable=False),
    Column("item_count", Integer, nullable=False),
    schema=REPORTING,
)
"""Mean RAGAs score per run and metric. The eval lane writes it next to eval.ragas_scores so the
quality dashboard can read it. The reporting schema also holds views, see migration 0002."""


@dataclass(frozen=True)
class ServingTables:
    metadata: MetaData
    chunks: Table
    validity: Table


def serving_tables(embedding_dim: int) -> ServingTables:
    """Serving schema. Content is stored once per chunk, validity rows say which versions see it."""
    serving_metadata = MetaData()
    chunks = Table(
        "chunks",
        serving_metadata,
        Column("chunk_id", String, primary_key=True),
        Column("doc_version", String, nullable=False, index=True),
        Column("page_start", Integer, nullable=False),
        Column("page_end", Integer, nullable=False),
        Column("section_path", JSONB, nullable=False),
        Column("text", Text, nullable=False),
        Column("kinds", JSONB, nullable=False),
        Column("token_count", Integer, nullable=False),
        Column("region_ids", JSONB, nullable=False),
        Column("ingestion_run_id", String, nullable=False),
        Column("embedding_model", String, nullable=False),
        Column("chunker_version", String, nullable=False),
        Column("embedding", Vector(embedding_dim), nullable=False),
        Column("tsv", TSVECTOR, Computed("to_tsvector('english', text)", persisted=True)),
        schema=SERVING,
    )
    Index(
        "chunks_embedding_hnsw",
        chunks.c.embedding,
        postgresql_using="hnsw",
        postgresql_ops={"embedding": "vector_cosine_ops"},
    )
    Index("chunks_tsv_gin", chunks.c.tsv, postgresql_using="gin")
    validity = Table(
        "chunk_validity",
        serving_metadata,
        Column("chunk_id", String, ForeignKey(chunks.c.chunk_id), primary_key=True),
        Column("valid_from_version", Integer, primary_key=True),
        Column("valid_to_version", Integer),
        Index("chunk_validity_versions", "valid_from_version", "valid_to_version"),
        schema=SERVING,
    )
    return ServingTables(serving_metadata, chunks, validity)


def sqlite_engine(url: str = "sqlite://") -> Engine:
    """SQLite engine with the schemas mapped away, for unit tests without Postgres."""
    connect_args = {"check_same_thread": False}
    engine = create_engine(url, connect_args=connect_args, poolclass=StaticPool)

    @event.listens_for(engine, "connect")
    def _enable_foreign_keys(connection, _record):
        connection.execute("PRAGMA foreign_keys=ON")

    return engine.execution_options(schema_translate_map=dict.fromkeys(SCHEMAS))
