"""Postgres holds the whole platform, knowledge base names and conversations.

Revision 0003, follows 0002. The Iceberg lake is gone. Its tiers and history tables become the
ingest, eval and ft schemas, and new ops tables for request facts, guard events and conversations.
The corpus tables and columns take their knowledge base names, and reporting.corpus_status becomes
reporting.kb_status. The old Iceberg catalog tables are dropped when they exist.
"""

from alembic import op

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None

NEW_SCHEMAS = ("ingest", "eval", "ft")

KB_STATUS_VIEW = """
CREATE VIEW reporting.kb_status AS
SELECT
    (SELECT version_id FROM registry.kb_aliases WHERE name = 'serving') AS serving_version,
    (SELECT version_id FROM registry.kb_aliases WHERE name = 'candidate') AS candidate_version,
    (SELECT max(published_at) FROM registry.kb_versions) AS last_published_at,
    (
        SELECT count(*) FROM registry.doc_versions AS d
        WHERE d.retracted_at IS NULL AND NOT EXISTS (
            SELECT 1 FROM registry.ingestion_runs AS r
            WHERE r.doc_version = d.doc_version AND r.status = 'succeeded'
        )
    ) AS pending_documents,
    (
        SELECT count(*) FROM registry.gate_reports
        WHERE requires_sme AND sme_decision IS NULL
    ) AS awaiting_sme
"""

CORPUS_STATUS_VIEW = """
CREATE VIEW reporting.corpus_status AS
SELECT
    (SELECT version_id FROM registry.corpus_aliases WHERE name = 'serving') AS serving_version,
    (SELECT version_id FROM registry.corpus_aliases WHERE name = 'candidate') AS candidate_version,
    (SELECT max(published_at) FROM registry.corpus_versions) AS last_published_at,
    (
        SELECT count(*) FROM registry.doc_versions AS d
        WHERE d.retracted_at IS NULL AND NOT EXISTS (
            SELECT 1 FROM registry.ingestion_runs AS r
            WHERE r.doc_version = d.doc_version AND r.status = 'succeeded'
        )
    ) AS pending_documents,
    (
        SELECT count(*) FROM registry.gate_reports
        WHERE requires_sme AND sme_decision IS NULL
    ) AS awaiting_sme
"""

RENAMES = [
    "DROP VIEW reporting.corpus_status",
    "ALTER TABLE registry.corpus_versions RENAME TO kb_versions",
    "ALTER INDEX registry.corpus_versions_pkey RENAME TO kb_versions_pkey",
    "ALTER TABLE registry.corpus_aliases RENAME TO kb_aliases",
    "ALTER INDEX registry.corpus_aliases_pkey RENAME TO kb_aliases_pkey",
    "ALTER TABLE ops.interactions RENAME COLUMN corpus_version TO kb_version",
    "ALTER TABLE reporting.ragas_summary RENAME COLUMN corpus_version TO kb_version",
    KB_STATUS_VIEW,
]

STATEMENTS = [
    "ALTER TABLE ops.interactions ADD COLUMN conversation_id VARCHAR",
    """
CREATE INDEX ix_ops_interactions_conversation_id ON ops.interactions (conversation_id)
""",
    """
CREATE TABLE ops.conversations (
    conversation_id VARCHAR NOT NULL,
    pseudo_user VARCHAR NOT NULL,
    started_at TIMESTAMP WITH TIME ZONE NOT NULL,
    last_active_at TIMESTAMP WITH TIME ZONE NOT NULL,
    PRIMARY KEY (conversation_id)
)
""",
    """
CREATE INDEX ix_ops_conversations_last_active_at ON ops.conversations (last_active_at)
""",
    """
CREATE INDEX ix_ops_conversations_pseudo_user ON ops.conversations (pseudo_user)
""",
    """
CREATE TABLE ops.request_facts (
    request_id VARCHAR NOT NULL,
    level VARCHAR NOT NULL,
    latency_ms FLOAT,
    e2e_ms FLOAT,
    tokens_in INTEGER,
    tokens_out INTEGER,
    guard_verdict VARCHAR,
    attachment_count INTEGER NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL,
    PRIMARY KEY (request_id)
)
""",
    """
CREATE INDEX ix_ops_request_facts_created_at ON ops.request_facts (created_at)
""",
    """
CREATE TABLE ops.guard_events (
    id SERIAL NOT NULL,
    request_id VARCHAR,
    detector VARCHAR NOT NULL,
    stage VARCHAR NOT NULL,
    category VARCHAR NOT NULL,
    score FLOAT NOT NULL,
    action VARCHAR NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL,
    PRIMARY KEY (id)
)
""",
    """
CREATE INDEX ix_ops_guard_events_created_at ON ops.guard_events (created_at)
""",
    """
CREATE INDEX ix_ops_guard_events_request_id ON ops.guard_events (request_id)
""",
    """
CREATE TABLE ingest.regions (
    ingestion_run_id VARCHAR NOT NULL,
    schema_version VARCHAR NOT NULL,
    producer VARCHAR NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL,
    region_id VARCHAR NOT NULL,
    doc_version VARCHAR NOT NULL,
    page_no INTEGER NOT NULL,
    kind VARCHAR NOT NULL,
    bbox JSONB,
    raw_text TEXT,
    image_uri VARCHAR,
    PRIMARY KEY (ingestion_run_id, region_id)
)
""",
    """
CREATE INDEX ix_ingest_regions_created_at ON ingest.regions (created_at)
""",
    """
CREATE INDEX ix_ingest_regions_doc_version ON ingest.regions (doc_version)
""",
    """
CREATE TABLE ingest.extracted_regions (
    ingestion_run_id VARCHAR NOT NULL,
    schema_version VARCHAR NOT NULL,
    producer VARCHAR NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL,
    region_id VARCHAR NOT NULL,
    kind VARCHAR NOT NULL,
    content TEXT NOT NULL,
    extractor JSONB NOT NULL,
    confidence FLOAT NOT NULL,
    PRIMARY KEY (ingestion_run_id, region_id)
)
""",
    """
CREATE INDEX ix_ingest_extracted_regions_created_at ON ingest.extracted_regions (created_at)
""",
    """
CREATE TABLE ingest.cleaned_pages (
    ingestion_run_id VARCHAR NOT NULL,
    schema_version VARCHAR NOT NULL,
    producer VARCHAR NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL,
    doc_version VARCHAR NOT NULL,
    page_no INTEGER NOT NULL,
    markdown TEXT NOT NULL,
    region_ids JSONB NOT NULL,
    flags JSONB NOT NULL,
    PRIMARY KEY (ingestion_run_id, doc_version, page_no)
)
""",
    """
CREATE INDEX ix_ingest_cleaned_pages_created_at ON ingest.cleaned_pages (created_at)
""",
    """
CREATE TABLE ingest.chunks (
    ingestion_run_id VARCHAR NOT NULL,
    schema_version VARCHAR NOT NULL,
    producer VARCHAR NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL,
    chunk_id VARCHAR NOT NULL,
    doc_version VARCHAR NOT NULL,
    embedding_model VARCHAR NOT NULL,
    chunker_version VARCHAR NOT NULL,
    page_start INTEGER NOT NULL,
    page_end INTEGER NOT NULL,
    section_path JSONB NOT NULL,
    text TEXT NOT NULL,
    kinds JSONB NOT NULL,
    token_count INTEGER NOT NULL,
    region_ids JSONB NOT NULL,
    embedding JSONB NOT NULL,
    PRIMARY KEY (ingestion_run_id, chunk_id)
)
""",
    """
CREATE INDEX ix_ingest_chunks_created_at ON ingest.chunks (created_at)
""",
    """
CREATE INDEX ix_ingest_chunks_doc_version ON ingest.chunks (doc_version)
""",
    """
CREATE TABLE eval.ragas_scores (
    id SERIAL NOT NULL,
    run_id VARCHAR NOT NULL,
    kb_version INTEGER,
    model_version VARCHAR,
    prompt_version VARCHAR,
    dataset VARCHAR NOT NULL,
    item_id VARCHAR NOT NULL,
    metric VARCHAR NOT NULL,
    score FLOAT NOT NULL,
    judge_model VARCHAR,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL,
    PRIMARY KEY (id)
)
""",
    """
CREATE INDEX ix_eval_ragas_scores_run_id ON eval.ragas_scores (run_id)
""",
    """
CREATE TABLE eval.test_cases (
    case_id VARCHAR NOT NULL,
    level INTEGER NOT NULL,
    question TEXT NOT NULL,
    source VARCHAR,
    reference_answer TEXT,
    course_code VARCHAR,
    topic VARCHAR,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL,
    PRIMARY KEY (case_id)
)
""",
    """
CREATE TABLE eval.test_runs (
    id SERIAL NOT NULL,
    run_id VARCHAR NOT NULL,
    case_id VARCHAR NOT NULL,
    response TEXT,
    level_reached VARCHAR,
    confidence FLOAT,
    escalated BOOLEAN NOT NULL,
    ragas JSONB NOT NULL,
    remediation TEXT,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL,
    PRIMARY KEY (id),
    FOREIGN KEY(case_id) REFERENCES eval.test_cases (case_id)
)
""",
    """
CREATE INDEX ix_eval_test_runs_run_id ON eval.test_runs (run_id)
""",
    """
CREATE TABLE ft.datasets (
    dataset_version VARCHAR NOT NULL,
    item_count INTEGER NOT NULL,
    manifest_sha256 VARCHAR(64) NOT NULL,
    export_uri VARCHAR NOT NULL,
    status VARCHAR NOT NULL,
    approved_by VARCHAR,
    approved_at TIMESTAMP WITH TIME ZONE,
    comment TEXT,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL,
    PRIMARY KEY (dataset_version)
)
""",
    """
CREATE TABLE ft.items (
    dataset_version VARCHAR NOT NULL,
    item_id VARCHAR NOT NULL,
    split VARCHAR NOT NULL,
    course_code VARCHAR,
    topic VARCHAR,
    question TEXT NOT NULL,
    answer TEXT NOT NULL,
    source VARCHAR NOT NULL,
    PRIMARY KEY (dataset_version, item_id),
    FOREIGN KEY(dataset_version) REFERENCES ft.datasets (dataset_version)
)
""",
    "DROP TABLE IF EXISTS public.iceberg_tables",
    "DROP TABLE IF EXISTS public.iceberg_namespace_properties",
]

DOWNGRADE = [
    "DROP TABLE IF EXISTS ops.guard_events",
    "DROP TABLE IF EXISTS ops.request_facts",
    "DROP TABLE IF EXISTS ops.conversations",
    "DROP INDEX IF EXISTS ops.ix_ops_interactions_conversation_id",
    "ALTER TABLE ops.interactions DROP COLUMN IF EXISTS conversation_id",
    "DROP VIEW reporting.kb_status",
    "ALTER TABLE reporting.ragas_summary RENAME COLUMN kb_version TO corpus_version",
    "ALTER TABLE ops.interactions RENAME COLUMN kb_version TO corpus_version",
    "ALTER INDEX registry.kb_aliases_pkey RENAME TO corpus_aliases_pkey",
    "ALTER TABLE registry.kb_aliases RENAME TO corpus_aliases",
    "ALTER INDEX registry.kb_versions_pkey RENAME TO corpus_versions_pkey",
    "ALTER TABLE registry.kb_versions RENAME TO corpus_versions",
    CORPUS_STATUS_VIEW,
]


def upgrade() -> None:
    for statement in RENAMES:
        op.execute(statement)
    for schema in NEW_SCHEMAS:
        op.execute(f"CREATE SCHEMA IF NOT EXISTS {schema}")
    for statement in STATEMENTS:
        op.execute(statement)


def downgrade() -> None:
    for schema in NEW_SCHEMAS:
        op.execute(f"DROP SCHEMA IF EXISTS {schema} CASCADE")
    for statement in DOWNGRADE:
        op.execute(statement)
