"""Base classes shared by every contract record."""

from pydantic import BaseModel, ConfigDict

SCHEMA_VERSION = "1.0"


class Model(BaseModel):
    """Immutable model that rejects unknown fields."""

    model_config = ConfigDict(frozen=True, extra="forbid")


class Record(Model):
    """A message exchanged between components.

    Every record states the schema version it follows and the component that produced it.
    """

    schema_version: str = SCHEMA_VERSION
    producer: str = "unknown"


class OfflineRecord(Record):
    """A record produced by the offline plane for one ingestion run."""

    ingestion_run_id: str


class OnlineRecord(Record):
    """A record produced while answering one student request."""

    request_id: str
