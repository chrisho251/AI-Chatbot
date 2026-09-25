"""Reporting schema for the monitoring dashboards.

Revision 0002, follows 0001. Grafana reads only this schema, through the grafana_reader role that
infra/local/postgres/init creates. The views aggregate ops and registry tables, so the reader never
sees rows about single students. The grants are skipped when the role does not exist, and
cover views that later migrations add to the schema.
"""

from alembic import op

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None

STATEMENTS = [
    "CREATE SCHEMA IF NOT EXISTS reporting",
    """
CREATE TABLE reporting.ragas_summary (
    run_id VARCHAR NOT NULL,
    metric VARCHAR NOT NULL,
    ts TIMESTAMP WITH TIME ZONE NOT NULL,
    dataset VARCHAR NOT NULL,
    corpus_version INTEGER,
    model_version VARCHAR,
    prompt_version VARCHAR,
    judge_model VARCHAR,
    mean_score FLOAT NOT NULL,
    item_count INTEGER NOT NULL,
    PRIMARY KEY (run_id, metric)
)
""",
    """
CREATE VIEW reporting.requests_daily AS
SELECT
    date_trunc('day', created_at) AS day,
    count(*) AS requests,
    count(*) FILTER (WHERE level = 'L1') AS l1,
    count(*) FILTER (WHERE level = 'L2') AS l2,
    count(*) FILTER (WHERE level = 'L3') AS l3,
    count(*) FILTER (WHERE used_external) AS used_external,
    count(*) FILTER (WHERE escalated) AS escalated,
    avg(confidence) AS mean_confidence
FROM ops.interactions
GROUP BY 1
""",
    """
CREATE VIEW reporting.escalation_daily AS
SELECT
    date_trunc('day', created_at) AS day,
    count(*) AS tickets,
    count(*) FILTER (WHERE answered_at IS NOT NULL) AS expert_answered,
    percentile_cont(0.5) WITHIN GROUP (ORDER BY external_response_ms) / 1000 AS external_p50_s,
    percentile_cont(0.95) WITHIN GROUP (ORDER BY external_response_ms) / 1000 AS external_p95_s,
    percentile_cont(0.5) WITHIN GROUP (ORDER BY extract(epoch FROM answered_at - created_at))
        AS expert_p50_s,
    percentile_cont(0.95) WITHIN GROUP (ORDER BY extract(epoch FROM answered_at - created_at))
        AS expert_p95_s
FROM ops.escalation_tickets
GROUP BY 1
""",
    """
CREATE VIEW reporting.tool_calls_daily AS
SELECT
    date_trunc('day', created_at) AS day,
    tool,
    verdict,
    count(*) AS calls,
    avg(duration_ms) AS mean_ms
FROM ops.tool_calls
GROUP BY 1, 2, 3
""",
    """
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
""",
    """
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'grafana_reader') THEN
        GRANT USAGE ON SCHEMA reporting TO grafana_reader;
        GRANT SELECT ON ALL TABLES IN SCHEMA reporting TO grafana_reader;
        ALTER DEFAULT PRIVILEGES IN SCHEMA reporting GRANT SELECT ON TABLES TO grafana_reader;
    END IF;
END
$$
""",
]


def upgrade() -> None:
    for statement in STATEMENTS:
        op.execute(statement)


def downgrade() -> None:
    op.execute("DROP SCHEMA IF EXISTS reporting CASCADE")
