# W6 embed

Worker-embed from Appendix A.4. Two roles in one package:

- **Offline (ingest):** structure-aware chunking and embedding of cleaned pages into a `ChunkSet`.
- **Online (answer time):** embeds the student question with the model pinned to the serving knowledge base version.

**Owner:** Lane B.
**Offline reads:** `ingest.cleaned_pages`. **Writes:** `ingest.chunks` through `chatbot_platform.ingest.write_chunk_set`.
**Online endpoint:** `POST /v1/embed`, `EmbedRequest` to `EmbedResult`.

## Files

- `chunker.py`: chunking rules and `CHUNKER_VERSION`.
- `encoder.py`: TEI or in-process embeddings.
- `job.py`: offline entrypoint.
- `query.py`, `serve.py`: online.

## Start here

1. `chunker.chunk_pages` with `samples.sample_clean_page`. This is the most important function of the lane, because chunk quality drives retrieval quality.
2. `encoder.LocalEmbedder`, then `job.run`. Check your output with the platform gate: `chatbot_platform.gate.check_chunk_ids` and `check_embeddings`.
3. `query.embed_query`.

## Test

```bash
uv run --package chatbot-w6-embed pytest workers/w6_embed/tests
```
