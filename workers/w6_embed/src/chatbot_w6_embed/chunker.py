"""Structure aware chunking. Stub owned by Lane B.

Purpose
Cut cleaned pages into chunks that retrieval can cite. Chunks follow sections and pages, and never
split an equation, a code listing or a table.

Input
The CleanPage records of one document version in page order, and the embedding model name.

Output
Chunks without embeddings. chunk_id comes from make_chunk_id with CHUNKER_VERSION and the
embedding model, so unchanged pages keep their ids across knowledge base versions. section_path
lists the
headings above the chunk, page_start and page_end cover every page the text came from.

What to build
Split on markdown headings, then pack paragraphs up to a token budget of about 400 tokens counted
with the tokenizer of the embedding model. Bump CHUNKER_VERSION whenever the rules change, that
forces a full rebuild of the knowledge base.

How to test
Pages from samples.sample_clean_page give chunks whose ids match make_chunk_id, an equation block
longer than the budget stays in one chunk, and running twice gives the same ids.
"""

from chatbot_contracts.knowledge_base import Chunk, CleanPage

CHUNKER_VERSION = "structure-v1"


def chunk_pages(pages: list[CleanPage], embedding_model: str) -> list[Chunk]:
    raise NotImplementedError("chunking is not written yet")
