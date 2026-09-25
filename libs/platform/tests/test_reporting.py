"""Reporting objects read by the Grafana quality dashboard. Views exist on Postgres only."""

from datetime import timedelta

import pytest
from sqlalchemy import insert, select, text

from chatbot_platform import sql


def _interaction(conn, request_id, level, created, *, escalated=False, used_external=False):
    conn.execute(
        insert(sql.interactions).values(
            request_id=request_id,
            pseudo_user="p",
            question_enc="c",
            level=level,
            confidence=0.9 if level == "L1" else 0.3,
            escalated=escalated,
            used_external=used_external,
            created_at=created,
        )
    )


@pytest.mark.integration
def test_requests_and_escalation_views(pg_engine):
    now = sql.utcnow()
    with pg_engine.begin() as conn:
        _interaction(conn, "r1", "L1", now)
        _interaction(conn, "r2", "L3", now, escalated=True, used_external=True)
        for ticket, external_ms, answered in (("t1", 2000.0, 600), ("t2", 4000.0, None)):
            conn.execute(
                insert(sql.escalation_tickets).values(
                    ticket_id=ticket,
                    request_id="r2",
                    pseudo_user="p",
                    question_enc="c",
                    confidence=0.3,
                    status="open",
                    context_ids=[],
                    external_results=[],
                    external_response_ms=external_ms,
                    created_at=now,
                    answered_at=now + timedelta(seconds=answered) if answered else None,
                )
            )
        conn.execute(
            insert(sql.tool_calls).values(
                request_id="r1",
                tool="w4_math",
                operation="mean",
                verdict="pass",
                duration_ms=12.0,
                created_at=now,
            )
        )
        requests = conn.execute(text("SELECT * FROM reporting.requests_daily")).mappings().one()
        escalation = conn.execute(text("SELECT * FROM reporting.escalation_daily")).mappings().one()
        tools = conn.execute(text("SELECT * FROM reporting.tool_calls_daily")).mappings().one()

    assert (requests["requests"], requests["l1"], requests["l3"], requests["escalated"]) == (
        2,
        1,
        1,
        1,
    )
    assert escalation["tickets"] == 2 and escalation["expert_answered"] == 1
    assert escalation["external_p50_s"] == pytest.approx(3.0)
    assert escalation["expert_p50_s"] == pytest.approx(600.0)
    assert (tools["tool"], tools["calls"]) == ("w4_math", 1)


@pytest.mark.integration
def test_corpus_status_view(pg_engine):
    with pg_engine.connect() as conn:
        status = conn.execute(text("SELECT * FROM reporting.corpus_status")).mappings().one()
    assert status["serving_version"] is None
    assert status["pending_documents"] == 0


def test_ragas_summary_table(platform):
    row = {
        "run_id": "run-1",
        "metric": "faithfulness",
        "ts": sql.utcnow(),
        "dataset": "golden",
        "mean_score": 0.87,
        "item_count": 30,
    }
    with platform.engine.begin() as conn:
        conn.execute(insert(sql.ragas_summary).values(row))
        score = conn.execute(select(sql.ragas_summary.c.mean_score)).scalar()
    assert score == pytest.approx(0.87)
