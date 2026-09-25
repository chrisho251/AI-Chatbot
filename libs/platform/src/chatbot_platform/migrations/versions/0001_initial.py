"""Initial registry, serving and ops schemas.

Revision 0001, the first one. The DDL is frozen here on purpose. Later schema changes go into new
revisions, never into this file.
"""

from alembic import context, op

from chatbot_platform.settings import PlatformSettings

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None

SCHEMAS = ("registry", "serving", "ops")

STATEMENTS = [
    """
CREATE TABLE ops.escalation_tickets (
    ticket_id VARCHAR NOT NULL,
    request_id VARCHAR NOT NULL,
    pseudo_user VARCHAR NOT NULL,
    question_enc TEXT NOT NULL,
    confidence FLOAT NOT NULL,
    status VARCHAR NOT NULL,
    context_ids JSONB NOT NULL,
    external_results JSONB NOT NULL,
    external_response_ms FLOAT,
    expert VARCHAR,
    answer TEXT,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL,
    answered_at TIMESTAMP WITH TIME ZONE,
    PRIMARY KEY (ticket_id)
)
""",
    """
CREATE INDEX ix_ops_escalation_tickets_created_at ON ops.escalation_tickets (created_at)
""",
    """
CREATE INDEX ix_ops_escalation_tickets_request_id ON ops.escalation_tickets (request_id)
""",
    """
CREATE TABLE ops.expert_rota (
    id SERIAL NOT NULL,
    expert VARCHAR NOT NULL,
    contact VARCHAR NOT NULL,
    starts_at TIMESTAMP WITH TIME ZONE NOT NULL,
    ends_at TIMESTAMP WITH TIME ZONE NOT NULL,
    PRIMARY KEY (id)
)
""",
    """
CREATE TABLE ops.external_candidates (
    candidate_id VARCHAR NOT NULL,
    url VARCHAR NOT NULL,
    snapshot_sha256 VARCHAR(64) NOT NULL,
    found_by VARCHAR NOT NULL,
    status VARCHAR NOT NULL,
    licence VARCHAR,
    course_code VARCHAR,
    topic VARCHAR,
    decided_by VARCHAR,
    decided_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL,
    PRIMARY KEY (candidate_id)
)
""",
    """
CREATE TABLE ops.interactions (
    request_id VARCHAR NOT NULL,
    pseudo_user VARCHAR NOT NULL,
    question_enc TEXT NOT NULL,
    answer TEXT,
    corpus_version INTEGER,
    model_version VARCHAR,
    prompt_version VARCHAR,
    confidence FLOAT,
    level VARCHAR,
    used_external BOOLEAN NOT NULL,
    escalated BOOLEAN NOT NULL,
    source_corrected BOOLEAN NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL,
    PRIMARY KEY (request_id)
)
""",
    """
CREATE INDEX ix_ops_interactions_created_at ON ops.interactions (created_at)
""",
    """
CREATE INDEX ix_ops_interactions_pseudo_user ON ops.interactions (pseudo_user)
""",
    """
CREATE TABLE ops.uploads (
    attachment_id VARCHAR NOT NULL,
    request_id VARCHAR NOT NULL,
    media_type VARCHAR NOT NULL,
    uri VARCHAR NOT NULL,
    sha256 VARCHAR(64) NOT NULL,
    size_bytes INTEGER NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL,
    PRIMARY KEY (attachment_id)
)
""",
    """
CREATE INDEX ix_ops_uploads_created_at ON ops.uploads (created_at)
""",
    """
CREATE INDEX ix_ops_uploads_request_id ON ops.uploads (request_id)
""",
    """
CREATE TABLE registry.corpus_aliases (
    name VARCHAR NOT NULL,
    version_id INTEGER NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL,
    PRIMARY KEY (name)
)
""",
    """
CREATE TABLE registry.corpus_versions (
    version_id INTEGER NOT NULL,
    parent_version INTEGER,
    doc_versions JSONB NOT NULL,
    embedding_model VARCHAR NOT NULL,
    chunker_version VARCHAR NOT NULL,
    status VARCHAR NOT NULL,
    gate_report_id VARCHAR,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL,
    published_at TIMESTAMP WITH TIME ZONE,
    PRIMARY KEY (version_id)
)
""",
    """
CREATE TABLE registry.doc_versions (
    doc_version VARCHAR NOT NULL,
    doc_id VARCHAR NOT NULL,
    sha256 VARCHAR(64) NOT NULL,
    source_type VARCHAR NOT NULL,
    course_code VARCHAR NOT NULL,
    source_id VARCHAR NOT NULL,
    raw_uri VARCHAR NOT NULL,
    licence VARCHAR,
    source_url VARCHAR,
    page_count INTEGER,
    supersedes VARCHAR,
    retracted_at TIMESTAMP WITH TIME ZONE,
    producer VARCHAR NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL,
    PRIMARY KEY (doc_version)
)
""",
    """
CREATE INDEX ix_registry_doc_versions_doc_id ON registry.doc_versions (doc_id)
""",
    """
CREATE INDEX ix_registry_doc_versions_supersedes ON registry.doc_versions (supersedes)
""",
    """
CREATE TABLE registry.gate_reports (
    report_id VARCHAR NOT NULL,
    version_id INTEGER NOT NULL,
    checks JSONB NOT NULL,
    requires_sme BOOLEAN NOT NULL,
    sme_decision VARCHAR,
    sme_by VARCHAR,
    sme_comment TEXT,
    sme_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL,
    PRIMARY KEY (report_id)
)
""",
    """
CREATE INDEX ix_registry_gate_reports_version_id ON registry.gate_reports (version_id)
""",
    """
CREATE TABLE ops.citations (
    id SERIAL NOT NULL,
    request_id VARCHAR NOT NULL,
    chunk_id VARCHAR,
    url VARCHAR,
    doc_version VARCHAR,
    page INTEGER,
    PRIMARY KEY (id),
    FOREIGN KEY(request_id) REFERENCES ops.interactions (request_id)
)
""",
    """
CREATE INDEX ix_ops_citations_chunk_id ON ops.citations (chunk_id)
""",
    """
CREATE TABLE ops.tool_calls (
    id SERIAL NOT NULL,
    request_id VARCHAR NOT NULL,
    tool VARCHAR NOT NULL,
    operation VARCHAR NOT NULL,
    language VARCHAR,
    verdict VARCHAR NOT NULL,
    duration_ms FLOAT NOT NULL,
    error TEXT,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL,
    PRIMARY KEY (id),
    FOREIGN KEY(request_id) REFERENCES ops.interactions (request_id)
)
""",
    """
CREATE TABLE registry.ingestion_runs (
    run_id VARCHAR NOT NULL,
    doc_version VARCHAR NOT NULL,
    dagster_run_id VARCHAR,
    status VARCHAR NOT NULL,
    started_at TIMESTAMP WITH TIME ZONE NOT NULL,
    finished_at TIMESTAMP WITH TIME ZONE,
    worker_digests JSONB NOT NULL,
    model_versions JSONB NOT NULL,
    PRIMARY KEY (run_id),
    FOREIGN KEY(doc_version) REFERENCES registry.doc_versions (doc_version)
)
""",
    """
CREATE TABLE serving.chunks (
    chunk_id VARCHAR NOT NULL,
    doc_version VARCHAR NOT NULL,
    page_start INTEGER NOT NULL,
    page_end INTEGER NOT NULL,
    section_path JSONB NOT NULL,
    text TEXT NOT NULL,
    kinds JSONB NOT NULL,
    token_count INTEGER NOT NULL,
    region_ids JSONB NOT NULL,
    ingestion_run_id VARCHAR NOT NULL,
    embedding_model VARCHAR NOT NULL,
    chunker_version VARCHAR NOT NULL,
    embedding VECTOR({dim}) NOT NULL,
    tsv TSVECTOR GENERATED ALWAYS AS (to_tsvector('english', text)) STORED,
    PRIMARY KEY (chunk_id)
)
""",
    """
CREATE INDEX chunks_embedding_hnsw ON serving.chunks USING hnsw (embedding vector_cosine_ops)
""",
    """
CREATE INDEX chunks_tsv_gin ON serving.chunks USING gin (tsv)
""",
    """
CREATE INDEX ix_serving_chunks_doc_version ON serving.chunks (doc_version)
""",
    """
CREATE TABLE serving.chunk_validity (
    chunk_id VARCHAR NOT NULL,
    valid_from_version INTEGER NOT NULL,
    valid_to_version INTEGER,
    PRIMARY KEY (chunk_id, valid_from_version),
    FOREIGN KEY(chunk_id) REFERENCES serving.chunks (chunk_id)
)
""",
    """
CREATE INDEX chunk_validity_versions ON serving.chunk_validity (valid_from_version, valid_to_version)
""",
]


def upgrade() -> None:
    dim = context.config.attributes.get("embedding_dim") or PlatformSettings().embedding_dim
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    for schema in SCHEMAS:
        op.execute(f"CREATE SCHEMA IF NOT EXISTS {schema}")
    for statement in STATEMENTS:
        op.execute(statement.replace("{dim}", str(int(dim))))


def downgrade() -> None:
    for schema in SCHEMAS:
        op.execute(f"DROP SCHEMA IF EXISTS {schema} CASCADE")
