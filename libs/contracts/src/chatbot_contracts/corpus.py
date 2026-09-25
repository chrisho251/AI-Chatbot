"""Records of the offline plane, from a registered file to a published corpus version."""

from pydantic import Field, model_validator

from chatbot_contracts.base import Model, OfflineRecord, Record
from chatbot_contracts.enums import CorpusStatus, RegionKind, SourceType


class DocumentVersion(Record):
    """One exact file of a source document, registered when it is uploaded.

    W1 fills page_count after layout analysis. supersedes names the version it corrects.
    """

    doc_id: str
    doc_version: str
    sha256: str = Field(min_length=64, max_length=64)
    source_type: SourceType
    course_code: str
    source_id: str
    raw_uri: str
    licence: str | None = None
    source_url: str | None = None
    page_count: int | None = Field(default=None, ge=1)
    supersedes: str | None = None


REGION_HANDLERS: dict[RegionKind, str] = {
    RegionKind.TEXT: "w5_clean",
    RegionKind.FIGURE: "w2_vision",
    RegionKind.SCAN: "w2_vision",
    RegionKind.TABLE: "w2_vision",
    RegionKind.EQUATION: "w4_math",
    RegionKind.CODE: "w3_code",
}
"""The worker that extracts each region kind. Text regions go straight to W5."""


class Region(OfflineRecord):
    """A typed area of one page, produced by W1 layout analysis."""

    region_id: str
    doc_version: str
    page_no: int = Field(ge=1)
    kind: RegionKind
    bbox: tuple[float, float, float, float] | None = None
    raw_text: str | None = None
    image_uri: str | None = None


class Extractor(Model):
    name: str
    version: str


class ExtractedRegion(OfflineRecord):
    """Content that W2, W3 or W4 extracted from one region."""

    region_id: str
    kind: RegionKind
    content: str
    extractor: Extractor
    confidence: float = Field(ge=0.0, le=1.0)


class PageFlags(Model):
    """Quality signals W5 records for one page. The quality gate reads them."""

    min_ocr_conf: float | None = Field(default=None, ge=0.0, le=1.0)
    pii_hits: int = Field(default=0, ge=0)
    pii_remaining: int = Field(default=0, ge=0)
    dup_of: str | None = None
    injection_hits: int = Field(default=0, ge=0)


class CleanPage(OfflineRecord):
    """One cleaned page in markdown. W5 writes exactly one per page, blank pages included."""

    doc_version: str
    page_no: int = Field(ge=1)
    markdown: str
    region_ids: list[str] = Field(default_factory=list)
    flags: PageFlags = Field(default_factory=PageFlags)


class Chunk(Model):
    """One retrievable piece of text. The embedding is left out when read back from search."""

    chunk_id: str
    doc_version: str
    page_start: int = Field(ge=1)
    page_end: int = Field(ge=1)
    section_path: list[str] = Field(default_factory=list)
    text: str
    kinds: list[RegionKind] = Field(default_factory=list)
    token_count: int = Field(ge=0)
    region_ids: list[str] = Field(default_factory=list)
    embedding: list[float] | None = None

    @model_validator(mode="after")
    def _pages_in_order(self) -> "Chunk":
        if self.page_end < self.page_start:
            raise ValueError("page_end must not be before page_start")
        return self


class ChunkSet(OfflineRecord):
    """All chunks W6 produced for one document version in one ingestion run."""

    doc_version: str
    embedding_model: str
    chunker_version: str
    chunks: list[Chunk]


class CorpusManifest(Record):
    """An immutable corpus version. The serving and candidate aliases point at one of these."""

    version_id: int = Field(ge=1)
    parent_version: int | None = None
    doc_versions: list[str]
    embedding_model: str
    chunker_version: str
    status: CorpusStatus
    gate_report_id: str | None = None
