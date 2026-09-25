"""Valid sample records for tests and local experiments.

Each lane builds realistic inputs here instead of waiting for the component that produces them.
Every factory accepts keyword arguments that override any field.
"""

import hashlib
import math
from collections.abc import Callable, Sequence
from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel

from chatbot_contracts.corpus import (
    Chunk,
    ChunkSet,
    CleanPage,
    CorpusManifest,
    DocumentVersion,
    ExtractedRegion,
    Extractor,
    PageFlags,
    Region,
)
from chatbot_contracts.enums import (
    CandidateOrigin,
    CleanOrigin,
    CodeLanguage,
    CorpusStatus,
    EscalationStatus,
    EventType,
    RegionKind,
    SourceType,
    Verdict,
)
from chatbot_contracts.escalation import EscalationTicket, StreamEvent
from chatbot_contracts.external import (
    ExternalCandidate,
    ExternalItem,
    ExternalSearchRequest,
    ExternalSearchResult,
)
from chatbot_contracts.ids import make_chunk_id, make_doc_id, make_doc_version, sha256_hex
from chatbot_contracts.query import (
    AskRequest,
    Attachment,
    Citation,
    CleanRequest,
    CleanResult,
    EmbedRequest,
    EmbedResult,
    GenerationRequest,
    GenerationResult,
    RetrievalRequest,
    RetrievalResult,
    RetrievedChunk,
    VisionRequest,
    VisionResult,
)
from chatbot_contracts.tools import CalcCheck, CalcResult, CodeResult, CodeTask

EMBEDDING_MODEL = "bge-m3"
CHUNKER_VERSION = "structure-v1"
EMBEDDING_DIM = 8
COURSE_CODE = "STAT 101"
SOURCE_ID = "textbook chapter 1"
FILE_SHA256 = sha256_hex(b"sample source file")
DOC_ID = make_doc_id(COURSE_CODE, SOURCE_ID)
DOC_VERSION = make_doc_version(DOC_ID, FILE_SHA256)
RUN_ID = "run-0001"
REQUEST_ID = "req-0001"
PAGE_TEXTS = (
    "The mean is the sum of the values divided by the number of values.",
    "A confidence interval gives a range of plausible values for a parameter.",
    "The odds ratio compares the odds of an outcome between two groups.",
)


def sample_embedding(text: str, dim: int = EMBEDDING_DIM) -> list[float]:
    """Deterministic unit vector derived from the text."""
    digest = hashlib.sha256(text.encode("utf-8")).digest()
    raw = [digest[i % len(digest)] - 127.5 for i in range(dim)]
    norm = math.sqrt(sum(value * value for value in raw))
    return [value / norm for value in raw]


def _build[M: BaseModel](model: type[M], defaults: dict[str, Any], overrides: dict[str, Any]) -> M:
    return model(**(defaults | overrides))


def sample_document_version(**overrides: Any) -> DocumentVersion:
    defaults = {
        "doc_id": DOC_ID,
        "doc_version": DOC_VERSION,
        "sha256": FILE_SHA256,
        "source_type": SourceType.TEXTBOOK,
        "course_code": COURSE_CODE,
        "source_id": SOURCE_ID,
        "raw_uri": f"s3://raw/{FILE_SHA256[:2]}/{FILE_SHA256}.pdf",
        "licence": "institution",
        "page_count": len(PAGE_TEXTS),
    }
    return _build(DocumentVersion, defaults, overrides)


def sample_region(**overrides: Any) -> Region:
    defaults = {
        "ingestion_run_id": RUN_ID,
        "region_id": "region-0001",
        "doc_version": DOC_VERSION,
        "page_no": 1,
        "kind": RegionKind.TEXT,
        "bbox": (0.0, 0.0, 100.0, 20.0),
        "raw_text": PAGE_TEXTS[0],
    }
    return _build(Region, defaults, overrides)


def sample_extracted_region(**overrides: Any) -> ExtractedRegion:
    defaults = {
        "ingestion_run_id": RUN_ID,
        "region_id": "region-0002",
        "kind": RegionKind.EQUATION,
        "content": r"\bar{x} = \frac{1}{n}\sum_{i=1}^{n} x_i",
        "extractor": Extractor(name="docling-formula", version="1"),
        "confidence": 0.93,
    }
    return _build(ExtractedRegion, defaults, overrides)


def sample_clean_page(**overrides: Any) -> CleanPage:
    page_no = overrides.get("page_no", 1)
    defaults = {
        "ingestion_run_id": RUN_ID,
        "doc_version": DOC_VERSION,
        "page_no": page_no,
        "markdown": PAGE_TEXTS[(page_no - 1) % len(PAGE_TEXTS)],
        "region_ids": [f"region-{page_no:04d}"],
        "flags": PageFlags(min_ocr_conf=0.97),
    }
    return _build(CleanPage, defaults, overrides)


def sample_chunk(
    text: str = PAGE_TEXTS[0],
    *,
    doc_version: str = DOC_VERSION,
    page_start: int = 1,
    page_end: int | None = None,
    dim: int = EMBEDDING_DIM,
    **overrides: Any,
) -> Chunk:
    """A chunk whose id and embedding are computed from its content, like W6 does."""
    end = page_start if page_end is None else page_end
    defaults = {
        "chunk_id": make_chunk_id(
            doc_version, page_start, end, text, CHUNKER_VERSION, EMBEDDING_MODEL
        ),
        "doc_version": doc_version,
        "page_start": page_start,
        "page_end": end,
        "section_path": ["Chapter 1", "Descriptive statistics"],
        "text": text,
        "kinds": [RegionKind.TEXT],
        "token_count": len(text.split()),
        "region_ids": [f"region-{page_start:04d}"],
        "embedding": sample_embedding(text, dim),
    }
    return _build(Chunk, defaults, overrides)


def sample_chunk_set(
    texts: Sequence[str] = PAGE_TEXTS,
    *,
    doc_version: str = DOC_VERSION,
    dim: int = EMBEDDING_DIM,
    **overrides: Any,
) -> ChunkSet:
    """One chunk per text, the text at position i sits on page i + 1."""
    chunks = [
        sample_chunk(text, doc_version=doc_version, page_start=page, dim=dim)
        for page, text in enumerate(texts, start=1)
    ]
    defaults = {
        "ingestion_run_id": RUN_ID,
        "doc_version": doc_version,
        "embedding_model": EMBEDDING_MODEL,
        "chunker_version": CHUNKER_VERSION,
        "chunks": chunks,
    }
    return _build(ChunkSet, defaults, overrides)


def sample_manifest(**overrides: Any) -> CorpusManifest:
    defaults = {
        "version_id": 1,
        "doc_versions": [DOC_VERSION],
        "embedding_model": EMBEDDING_MODEL,
        "chunker_version": CHUNKER_VERSION,
        "status": CorpusStatus.CANDIDATE,
    }
    return _build(CorpusManifest, defaults, overrides)


def sample_attachment(**overrides: Any) -> Attachment:
    sha = sha256_hex(b"sample photo")
    defaults = {
        "request_id": REQUEST_ID,
        "attachment_id": "att-0001",
        "media_type": "image/jpeg",
        "uri": f"s3://uploads/2026/09/25/{REQUEST_ID}/att-0001",
        "sha256": sha,
        "size_bytes": 20480,
    }
    return _build(Attachment, defaults, overrides)


def sample_ask_request(**overrides: Any) -> AskRequest:
    defaults = {
        "request_id": REQUEST_ID,
        "pseudo_user": "pseudo-7f3a",
        "question": "How do I compute a 95 percent confidence interval for a mean?",
    }
    return _build(AskRequest, defaults, overrides)


def sample_vision_request(**overrides: Any) -> VisionRequest:
    defaults = {"request_id": REQUEST_ID, "attachment": sample_attachment()}
    return _build(VisionRequest, defaults, overrides)


def sample_vision_result(**overrides: Any) -> VisionResult:
    defaults = {
        "request_id": REQUEST_ID,
        "text": "Find the mean of 4, 8 and 15.",
        "latex": [r"\bar{x}"],
        "detected_kind": "problem_set",
        "confidence": 0.88,
    }
    return _build(VisionResult, defaults, overrides)


def sample_clean_request(**overrides: Any) -> CleanRequest:
    defaults = {
        "request_id": REQUEST_ID,
        "text": sample_ask_request().question,
        "origin": CleanOrigin.QUESTION,
    }
    return _build(CleanRequest, defaults, overrides)


def sample_clean_result(**overrides: Any) -> CleanResult:
    defaults = {"request_id": REQUEST_ID, "text": sample_ask_request().question}
    return _build(CleanResult, defaults, overrides)


def sample_embed_request(**overrides: Any) -> EmbedRequest:
    defaults = {
        "request_id": REQUEST_ID,
        "texts": [sample_ask_request().question],
        "corpus_version": 1,
    }
    return _build(EmbedRequest, defaults, overrides)


def sample_embed_result(**overrides: Any) -> EmbedResult:
    defaults = {
        "request_id": REQUEST_ID,
        "vectors": [sample_embedding(sample_ask_request().question)],
        "embedding_model": EMBEDDING_MODEL,
    }
    return _build(EmbedResult, defaults, overrides)


def sample_retrieval_request(**overrides: Any) -> RetrievalRequest:
    question = sample_ask_request().question
    defaults = {
        "request_id": REQUEST_ID,
        "question": question,
        "query_vector": sample_embedding(question),
        "corpus_version": 1,
    }
    return _build(RetrievalRequest, defaults, overrides)


def sample_retrieved_chunk(**overrides: Any) -> RetrievedChunk:
    chunk = sample_chunk(PAGE_TEXTS[1], page_start=2)
    defaults = {
        "chunk_id": chunk.chunk_id,
        "doc_version": chunk.doc_version,
        "page_start": chunk.page_start,
        "page_end": chunk.page_end,
        "text": chunk.text,
        "dense": 0.82,
        "lexical": 0.4,
        "rerank": 0.91,
    }
    return _build(RetrievedChunk, defaults, overrides)


def sample_retrieval_result(**overrides: Any) -> RetrievalResult:
    defaults = {
        "request_id": REQUEST_ID,
        "chunks": [sample_retrieved_chunk()],
        "sufficiency": 0.86,
        "timings_ms": {"dense": 12.0, "lexical": 4.0, "rerank": 35.0},
    }
    return _build(RetrievalResult, defaults, overrides)


def sample_generation_request(**overrides: Any) -> GenerationRequest:
    defaults = {
        "request_id": REQUEST_ID,
        "question": sample_ask_request().question,
        "contexts": [sample_retrieved_chunk()],
        "model_version": "qwen3-4b-instruct",
        "prompt_version": "answer-v1",
    }
    return _build(GenerationRequest, defaults, overrides)


def sample_generation_result(**overrides: Any) -> GenerationResult:
    context = sample_retrieved_chunk()
    defaults = {
        "request_id": REQUEST_ID,
        "answer": "Take the sample mean plus or minus 1.96 standard errors [1].",
        "citations": [Citation(chunk_id=context.chunk_id, doc_version=context.doc_version, page=2)],
        "tokens_in": 850,
        "tokens_out": 120,
    }
    return _build(GenerationResult, defaults, overrides)


def sample_calc_check(**overrides: Any) -> CalcCheck:
    defaults = {
        "request_id": REQUEST_ID,
        "operation": "mean",
        "expression": "(4 + 8 + 15) / 3",
    }
    return _build(CalcCheck, defaults, overrides)


def sample_calc_result(**overrides: Any) -> CalcResult:
    defaults = {"request_id": REQUEST_ID, "valid": True, "explanation": "27 / 3 = 9", "value": 9.0}
    return _build(CalcResult, defaults, overrides)


def sample_code_task(**overrides: Any) -> CodeTask:
    defaults = {
        "request_id": REQUEST_ID,
        "language": CodeLanguage.R,
        "task": "Compute the mean of 4, 8 and 15.",
        "expected": "9",
    }
    return _build(CodeTask, defaults, overrides)


def sample_code_result(**overrides: Any) -> CodeResult:
    defaults = {
        "request_id": REQUEST_ID,
        "code": "mean(c(4, 8, 15))",
        "stdout": "[1] 9",
        "verdict": Verdict.PASS,
        "duration_ms": 180.0,
        "values": {"mean": 9.0},
    }
    return _build(CodeResult, defaults, overrides)


def sample_external_item(**overrides: Any) -> ExternalItem:
    defaults = {
        "url": "https://openstax.org/books/introductory-statistics/pages/8-practice",
        "title": "Confidence intervals practice",
        "snippet": "Construct a 95 percent confidence interval for the population mean.",
        "score": 0.71,
        "licence": "CC BY 4.0",
    }
    return _build(ExternalItem, defaults, overrides)


def sample_external_search_request(**overrides: Any) -> ExternalSearchRequest:
    defaults = {
        "request_id": REQUEST_ID,
        "query": "confidence interval for a mean exercise with answer",
        "topics": ["confidence intervals"],
    }
    return _build(ExternalSearchRequest, defaults, overrides)


def sample_external_search_result(**overrides: Any) -> ExternalSearchResult:
    defaults = {"request_id": REQUEST_ID, "items": [sample_external_item()]}
    return _build(ExternalSearchResult, defaults, overrides)


def sample_external_candidate(**overrides: Any) -> ExternalCandidate:
    defaults = {
        "candidate_id": "cand-0001",
        "url": sample_external_item().url,
        "snapshot_sha256": sha256_hex(b"sample snapshot"),
        "found_by": CandidateOrigin.ANSWER_TIME,
        "licence": "CC BY 4.0",
        "course_code": COURSE_CODE,
        "topic": "confidence intervals",
    }
    return _build(ExternalCandidate, defaults, overrides)


def sample_escalation_ticket(**overrides: Any) -> EscalationTicket:
    defaults = {
        "request_id": REQUEST_ID,
        "ticket_id": "ticket-0001",
        "pseudo_user": "pseudo-7f3a",
        "question": sample_ask_request().question,
        "confidence": 0.31,
        "status": EscalationStatus.OPEN,
        "created_at": datetime(2026, 9, 25, 9, 0, tzinfo=UTC),
        "context_ids": [sample_retrieved_chunk().chunk_id],
    }
    return _build(EscalationTicket, defaults, overrides)


def sample_stream_event(**overrides: Any) -> StreamEvent:
    defaults = {"request_id": REQUEST_ID, "type": EventType.ANSWER_DELTA, "text": "Take the "}
    return _build(StreamEvent, defaults, overrides)


SAMPLES: dict[type[BaseModel], Callable[..., BaseModel]] = {
    DocumentVersion: sample_document_version,
    Region: sample_region,
    ExtractedRegion: sample_extracted_region,
    CleanPage: sample_clean_page,
    Chunk: sample_chunk,
    ChunkSet: sample_chunk_set,
    CorpusManifest: sample_manifest,
    Attachment: sample_attachment,
    AskRequest: sample_ask_request,
    VisionRequest: sample_vision_request,
    VisionResult: sample_vision_result,
    CleanRequest: sample_clean_request,
    CleanResult: sample_clean_result,
    EmbedRequest: sample_embed_request,
    EmbedResult: sample_embed_result,
    RetrievalRequest: sample_retrieval_request,
    RetrievedChunk: sample_retrieved_chunk,
    RetrievalResult: sample_retrieval_result,
    GenerationRequest: sample_generation_request,
    GenerationResult: sample_generation_result,
    CalcCheck: sample_calc_check,
    CalcResult: sample_calc_result,
    CodeTask: sample_code_task,
    CodeResult: sample_code_result,
    ExternalItem: sample_external_item,
    ExternalSearchRequest: sample_external_search_request,
    ExternalSearchResult: sample_external_search_result,
    ExternalCandidate: sample_external_candidate,
    EscalationTicket: sample_escalation_ticket,
    StreamEvent: sample_stream_event,
}
"""One factory per record type, used by tests that must cover every contract."""
