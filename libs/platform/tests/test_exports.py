from chatbot_platform.exports import export_rows, read_export
from chatbot_platform.settings import EXPORTS_BUCKET
from chatbot_platform.storage import split_uri

ROWS = [
    {"item_id": "i1", "question": "What is a mean?", "answer": "The sum divided by the count."},
    {"item_id": "i2", "question": "What is a median?", "answer": "The middle value."},
]


def test_export_is_written_once_and_reads_back(platform):
    first = export_rows(platform.store, "ft/datasets", ROWS)
    second = export_rows(platform.store, "ft/datasets", ROWS)
    bucket, key = split_uri(first.uri)
    assert first == second
    assert (bucket, first.rows) == (EXPORTS_BUCKET, 2)
    assert key == f"ft/datasets/{first.sha256}.parquet"
    assert platform.store.list_keys(EXPORTS_BUCKET) == [key]
    assert read_export(platform.store, first.uri) == ROWS


def test_different_rows_get_a_different_file(platform):
    first = export_rows(platform.store, "ft/datasets", ROWS)
    second = export_rows(platform.store, "ft/datasets", ROWS[:1])
    assert first.uri != second.uri
