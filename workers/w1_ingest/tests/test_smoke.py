import pytest

from chatbot_w1_ingest import job


def test_job_needs_run_and_document():
    with pytest.raises(SystemExit):
        job.main([])
