import boto3
import pytest
from moto import mock_aws

from chatbot_platform.storage import LocalFsObjectStore, S3ObjectStore, split_uri


@pytest.fixture(params=["local", "s3"])
def store(request, tmp_path):
    if request.param == "local":
        yield LocalFsObjectStore(tmp_path)
        return
    with mock_aws():
        client = boto3.client("s3", region_name="us-east-1")
        yield S3ObjectStore(None, "key", "secret", "us-east-1", client=client)


def test_put_get_list_delete(store):
    store.ensure_bucket("raw")
    uri = store.put("raw", "ab/abc.pdf", b"data")
    assert uri == "s3://raw/ab/abc.pdf"
    assert split_uri(uri) == ("raw", "ab/abc.pdf")
    assert store.get("raw", "ab/abc.pdf") == b"data"
    assert store.exists("raw", "ab/abc.pdf")
    store.put("raw", "cd/other.pdf", b"x")
    assert store.list_keys("raw", "ab/") == ["ab/abc.pdf"]
    store.delete("raw", "ab/abc.pdf")
    assert not store.exists("raw", "ab/abc.pdf")


def test_ensure_bucket_is_idempotent(store):
    store.ensure_bucket("raw")
    store.ensure_bucket("raw")
    assert store.list_keys("raw") == []


@pytest.mark.parametrize("key", ["../escape", "/absolute", ""])
def test_unsafe_keys_are_rejected(store, key):
    store.ensure_bucket("raw")
    with pytest.raises(ValueError):
        store.put("raw", key, b"x")


def test_split_uri_rejects_other_schemes():
    with pytest.raises(ValueError):
        split_uri("file:///tmp/x")
