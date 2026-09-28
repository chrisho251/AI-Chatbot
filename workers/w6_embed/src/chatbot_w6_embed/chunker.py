"""Structure aware chunking.

Purpose
Cut cleaned pages into chunks that retrieval can cite. Chunks follow sections and pages, and never
split an equation, a code listing or a table.

Input
The CleanPage records of one document version in page order, and the embedding model name.

Output
Chunks without embeddings. chunk_id comes from make_chunk_id with CHUNKER_VERSION and the
embedding model, so unchanged pages keep their ids across knowledge base versions. section_path
lists the headings above the chunk, page_start and page_end cover every page the text came from.

What to build
Split on markdown headings, then pack paragraphs up to a token budget of about 400 tokens counted
with the tokenizer of the embedding model. Bump CHUNKER_VERSION whenever the rules change, that
forces a full rebuild of the knowledge base.

How to test
Pages from samples.sample_clean_page give chunks whose ids match make_chunk_id, an equation block
longer than the budget stays in one chunk, and running twice gives the same ids.
"""

import re

from sentence_transformers import SentenceTransformer

from chatbot_contracts.enums import RegionKind
from chatbot_contracts.ids import make_chunk_id
from chatbot_contracts.knowledge_base import Chunk, CleanPage

CHUNKER_VERSION = "structure-v1"
TOKEN_BUDGET = 400

HEADING_PATTERN = re.compile(r"^(#{1,6})\s+(.+)$", re.MULTILINE)
EQUATION_BLOCK_PATTERN = re.compile(
    r"(\$\$.*?\$\$|\\\[.*?\\\]|\\begin\{.*?\}.*?\\end\{.*?\})", re.DOTALL
)
CODE_BLOCK_PATTERN = re.compile(r"(```.*?```|~~~.*?~~~)", re.DOTALL)
TABLE_PATTERN = re.compile(r"(\|.*?\|(?:\n\|.*?\|)+)", re.MULTILINE)

PROTECTED_PATTERNS = [
    (EQUATION_BLOCK_PATTERN, RegionKind.EQUATION),
    (CODE_BLOCK_PATTERN, RegionKind.CODE),
    (TABLE_PATTERN, RegionKind.TABLE),
]


def _get_tokenizer(model_name: str):
    model = SentenceTransformer(model_name)
    return model.tokenizer


def _count_tokens(text: str, tokenizer) -> int:
    return len(tokenizer.encode(text, add_special_tokens=False))


def _extract_protected_blocks(text: str) -> tuple[str, list[tuple[str, RegionKind, int, int]]]:
    blocks: list[tuple[str, RegionKind, int, int]] = []
    placeholder_text = text
    offset = 0

    for pattern, kind in PROTECTED_PATTERNS:
        for match in pattern.finditer(text):
            start, end = match.span()
            block_text = match.group(0)
            adj_start = start + offset
            adj_end = end + offset
            placeholder = f"<<<PROTECTED_{kind.value}_{len(blocks)}>>>"
            placeholder_text = (
                placeholder_text[:adj_start] + placeholder + placeholder_text[adj_end:]
            )
            offset += len(placeholder) - (end - start)
            blocks.append((block_text, kind, start, end))

    return placeholder_text, blocks


def _restore_protected_blocks(text: str, blocks: list[tuple[str, RegionKind, int, int]]) -> str:
    result = text
    for i, (block_text, kind, _, _) in enumerate(blocks):
        placeholder = f"<<<PROTECTED_{kind.value}_{i}>>>"
        result = result.replace(placeholder, block_text)
    return result


def _split_by_headings(text: str) -> list[tuple[list[str], str]]:
    sections = []
    current_path: list[str] = []
    current_content: list[str] = []

    lines = text.split("\n")
    for line in lines:
        heading_match = HEADING_PATTERN.match(line)
        if heading_match:
            if current_content:
                sections.append((current_path.copy(), "\n".join(current_content).strip()))
                current_content = []
            level = len(heading_match.group(1))
            heading_text = heading_match.group(2).strip()
            current_path = current_path[:level - 1] + [heading_text]
        else:
            current_content.append(line)

    if current_content:
        sections.append((current_path.copy(), "\n".join(current_content).strip()))

    return sections


def _pack_paragraphs(
    paragraphs: list[str],
    section_path: list[str],
    page_no: int,
    doc_version: str,
    embedding_model: str,
    tokenizer,
) -> list[Chunk]:
    chunks = []
    current_chunk_paras: list[str] = []
    current_tokens = 0
    chunk_page_start = page_no

    for para in paragraphs:
        para = para.strip()
        if not para:
            continue

        para_tokens = _count_tokens(para, tokenizer)

        if para_tokens > TOKEN_BUDGET:
            if current_chunk_paras:
                chunk_text = "\n\n".join(current_chunk_paras)
                chunk_id = make_chunk_id(
                    doc_version, chunk_page_start, page_no, chunk_text,
                    CHUNKER_VERSION, embedding_model
                )
                chunks.append(Chunk(
                    chunk_id=chunk_id,
                    doc_version=doc_version,
                    page_start=chunk_page_start,
                    page_end=page_no,
                    section_path=section_path.copy(),
                    text=chunk_text,
                    kinds=[RegionKind.TEXT],
                    token_count=current_tokens,
                    region_ids=[],
                ))
                current_chunk_paras = []
                current_tokens = 0
                chunk_page_start = page_no

            chunk_id = make_chunk_id(
                doc_version, page_no, page_no, para,
                CHUNKER_VERSION, embedding_model
            )
            chunks.append(Chunk(
                chunk_id=chunk_id,
                doc_version=doc_version,
                page_start=page_no,
                page_end=page_no,
                section_path=section_path.copy(),
                text=para,
                kinds=[RegionKind.TEXT],
                token_count=para_tokens,
                region_ids=[],
            ))
            continue

        if current_tokens + para_tokens > TOKEN_BUDGET and current_chunk_paras:
            chunk_text = "\n\n".join(current_chunk_paras)
            chunk_id = make_chunk_id(
                doc_version, chunk_page_start, page_no, chunk_text,
                CHUNKER_VERSION, embedding_model
            )
            chunks.append(Chunk(
                chunk_id=chunk_id,
                doc_version=doc_version,
                page_start=chunk_page_start,
                page_end=page_no,
                section_path=section_path.copy(),
                text=chunk_text,
                kinds=[RegionKind.TEXT],
                token_count=current_tokens,
                region_ids=[],
            ))
            current_chunk_paras = [para]
            current_tokens = para_tokens
            chunk_page_start = page_no
        else:
            current_chunk_paras.append(para)
            current_tokens += para_tokens

    if current_chunk_paras:
        chunk_text = "\n\n".join(current_chunk_paras)
        chunk_id = make_chunk_id(
            doc_version, chunk_page_start, page_no, chunk_text,
            CHUNKER_VERSION, embedding_model
        )
        chunks.append(Chunk(
            chunk_id=chunk_id,
            doc_version=doc_version,
            page_start=chunk_page_start,
            page_end=page_no,
            section_path=section_path.copy(),
            text=chunk_text,
            kinds=[RegionKind.TEXT],
            token_count=current_tokens,
            region_ids=[],
        ))

    return chunks


def chunk_pages(pages: list[CleanPage], embedding_model: str) -> list[Chunk]:
    if not pages:
        return []

    tokenizer = _get_tokenizer(embedding_model)

    all_chunks = []

    for page in pages:
        placeholder_text, protected_blocks = _extract_protected_blocks(page.markdown)
        sections = _split_by_headings(placeholder_text)

        for section_path, content in sections:
            if not content.strip():
                continue

            restored_content = _restore_protected_blocks(content, protected_blocks)
            paragraphs = [p.strip() for p in restored_content.split("\n\n") if p.strip()]

            page_chunks = _pack_paragraphs(
                paragraphs=paragraphs,
                section_path=section_path,
                page_no=page.page_no,
                doc_version=page.doc_version,
                embedding_model=embedding_model,
                tokenizer=tokenizer,
            )
            all_chunks.extend(page_chunks)

    return all_chunks