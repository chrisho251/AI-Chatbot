# W8 gen

Worker-gen from Appendix A.4. It writes the cited answer from retrieved context and computed results.

**Owner:** Lane C.
**Endpoints:** `POST /v1/generate` (`routes.GENERATE`) and `POST /v1/generate/stream` (`routes.GENERATE_STREAM`, server-sent events).
**Calls:** the LLM server (`chatbot_common.llm.ChatClient`), W4 (`routes.CALC`) and W3 (`routes.CODE`).

## Files

- `generate.py`: the flow.
- `prompt.py`: the versioned grounded prompt.
- `tools.py`: tool calls to W3 and W4.
- `citations.py`: citation markers to `Citation` records.

## Start here

1. `prompt.build_messages` and `citations.parse`, both pure.
2. `generate.generate_stream` with a faked LLM.
3. `tools.run` with faked W3 and W4.

## Test

```bash
uv run --package chatbot-w8-gen pytest workers/w8_gen/tests
```
