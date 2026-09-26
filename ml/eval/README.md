# Eval

RAGAs evaluation (Appendix A.6), the golden set, the retrieval and RAGAs checks of the quality gate, and the internal testing levels of Appendix C.

**Owner:** Lane D.
**Writes:** the Postgres tables `eval.ragas_scores`, `eval.test_cases`, `eval.test_runs` (defined in `chatbot_platform.sql`), and `reporting.ragas_summary` for the dashboard.
**Plugs into:** `chatbot_platform.gate` (see `gate_checks.py`) and the Dagster schedules of Lane A.

## Files

- `golden_set.py`: the reviewed questions with reference answers.
- `ragas_runner.py`: the four metrics with the self-hosted judge.
- `gate_checks.py`: replaces the two skipped placeholders in the gate.
- `test_runs.py`: Appendix C test cycles.

## Start here

1. A first golden set of about 30 items per course, reviewed by an SME.
2. `ragas_runner.run` against a faked orchestrator, then against the real one.
3. `gate_checks`, so a bad knowledge base version can no longer publish.

## Test

```bash
uv run --package chatbot-eval pytest ml/eval/tests
```
