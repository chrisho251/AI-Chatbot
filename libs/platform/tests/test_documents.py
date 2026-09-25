import pytest

from chatbot_contracts.enums import SourceType
from chatbot_platform.errors import VersioningError
from chatbot_platform.models import RunStatus
from chatbot_platform.settings import RAW_BUCKET
from chatbot_platform.storage import split_uri


def test_upload_stores_raw_file_and_registers_version(platform, upload):
    document = upload(b"first edition")
    bucket, key = split_uri(document.raw_uri)
    assert bucket == RAW_BUCKET
    assert platform.store.get(bucket, key) == b"first edition"
    assert document.supersedes is None
    assert platform.registry.pending_doc_versions() == [document.doc_version]


def test_same_file_twice_returns_the_same_version(platform, upload):
    first = upload(b"same bytes")
    second = upload(b"same bytes")
    assert first == second
    assert len(platform.registry.pending_doc_versions()) == 1


def test_new_file_for_same_source_supersedes_the_previous(platform, upload):
    old = upload(b"first edition")
    new = upload(b"corrected edition")
    assert new.doc_version != old.doc_version
    assert new.supersedes == old.doc_version
    assert platform.registry.superseded_by([old.doc_version]) == {old.doc_version: new.doc_version}


def test_external_exercise_needs_a_licence(platform, upload):
    with pytest.raises(VersioningError):
        upload(b"web page", source_type=SourceType.EXTERNAL_EXERCISE)


def test_successful_run_removes_version_from_pending(platform, upload):
    document = upload(b"notes")
    run_id = platform.registry.start_run(document.doc_version, dagster_run_id="dagster-1")
    assert platform.registry.pending_doc_versions() == [document.doc_version]
    platform.registry.finish_run(run_id, RunStatus.SUCCEEDED, {"w1_ingest": "sha256:abc"})
    assert platform.registry.pending_doc_versions() == []


def test_retracted_version_is_not_pending(platform, upload):
    document = upload(b"withdrawn")
    platform.registry.retract(document.doc_version)
    assert platform.registry.pending_doc_versions() == []
    assert platform.registry.retracted([document.doc_version]) == {document.doc_version}
