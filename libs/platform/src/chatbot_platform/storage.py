"""Object store port with a local folder adapter and an S3 adapter.

The S3 adapter serves both SeaweedFS on a laptop and Amazon S3 in the cloud.
Object uris always look like s3 uris, so stored uris stay valid when the backend changes.
"""

import os
import tempfile
from pathlib import Path, PurePosixPath
from typing import Any, Protocol

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError


class ObjectStore(Protocol):
    def ensure_bucket(self, bucket: str) -> None: ...

    def put(self, bucket: str, key: str, data: bytes) -> str:
        """Store the bytes and return the object uri."""
        ...

    def get(self, bucket: str, key: str) -> bytes: ...

    def exists(self, bucket: str, key: str) -> bool: ...

    def delete(self, bucket: str, key: str) -> None: ...

    def list_keys(self, bucket: str, prefix: str = "") -> list[str]: ...


def object_uri(bucket: str, key: str) -> str:
    return f"s3://{bucket}/{key}"


def split_uri(uri: str) -> tuple[str, str]:
    """Bucket and key of an object uri."""
    if not uri.startswith("s3://"):
        raise ValueError(f"not an object uri: {uri}")
    bucket, _, key = uri.removeprefix("s3://").partition("/")
    if not bucket or not key:
        raise ValueError(f"object uri needs a bucket and a key: {uri}")
    return bucket, key


def _check_key(key: str) -> None:
    parts = PurePosixPath(key).parts
    if not parts or ".." in parts or key.startswith("/"):
        raise ValueError(f"unsafe object key: {key}")


class LocalFsObjectStore:
    """Stores each bucket as a folder under root. Used for tests and quick experiments."""

    def __init__(self, root: Path) -> None:
        self.root = root

    def _path(self, bucket: str, key: str) -> Path:
        _check_key(key)
        return self.root / bucket / key

    def ensure_bucket(self, bucket: str) -> None:
        (self.root / bucket).mkdir(parents=True, exist_ok=True)

    def put(self, bucket: str, key: str, data: bytes) -> str:
        path = self._path(bucket, key)
        path.parent.mkdir(parents=True, exist_ok=True)
        fd, tmp = tempfile.mkstemp(dir=path.parent)
        with os.fdopen(fd, "wb") as handle:
            handle.write(data)
        os.replace(tmp, path)
        return object_uri(bucket, key)

    def get(self, bucket: str, key: str) -> bytes:
        return self._path(bucket, key).read_bytes()

    def exists(self, bucket: str, key: str) -> bool:
        return self._path(bucket, key).is_file()

    def delete(self, bucket: str, key: str) -> None:
        self._path(bucket, key).unlink(missing_ok=True)

    def list_keys(self, bucket: str, prefix: str = "") -> list[str]:
        base = self.root / bucket
        if not base.is_dir():
            return []
        keys = (path.relative_to(base).as_posix() for path in base.rglob("*") if path.is_file())
        return sorted(key for key in keys if key.startswith(prefix))


class S3ObjectStore:
    """S3 API adapter. Path style addressing keeps it compatible with SeaweedFS."""

    def __init__(
        self,
        endpoint_url: str | None,
        access_key: str,
        secret_key: str,
        region: str,
        client: Any = None,
    ) -> None:
        self.client = client or boto3.client(
            "s3",
            endpoint_url=endpoint_url,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            region_name=region,
            config=Config(s3={"addressing_style": "path"}),
        )

    def ensure_bucket(self, bucket: str) -> None:
        try:
            self.client.head_bucket(Bucket=bucket)
        except ClientError:
            self.client.create_bucket(Bucket=bucket)

    def put(self, bucket: str, key: str, data: bytes) -> str:
        _check_key(key)
        self.client.put_object(Bucket=bucket, Key=key, Body=data)
        return object_uri(bucket, key)

    def get(self, bucket: str, key: str) -> bytes:
        return self.client.get_object(Bucket=bucket, Key=key)["Body"].read()

    def exists(self, bucket: str, key: str) -> bool:
        try:
            self.client.head_object(Bucket=bucket, Key=key)
        except ClientError as error:
            if error.response["Error"]["Code"] in ("404", "NoSuchKey", "NotFound"):
                return False
            raise
        return True

    def delete(self, bucket: str, key: str) -> None:
        self.client.delete_object(Bucket=bucket, Key=key)

    def list_keys(self, bucket: str, prefix: str = "") -> list[str]:
        paginator = self.client.get_paginator("list_objects_v2")
        keys = []
        for page in paginator.paginate(Bucket=bucket, Prefix=prefix):
            keys.extend(item["Key"] for item in page.get("Contents", []))
        return sorted(keys)
