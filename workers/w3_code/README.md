# W3 code

Worker-code from Appendix A.4. Two roles in one package, plus a separate sandbox image:

- **Offline (ingest):** keeps R, SPSS and Python listings verbatim with a language tag.
- **Online (answer time):** generates R, Python or Excel formulas for an exercise, runs them and checks the result against the draft answer.
- **Sandbox (`sandbox/`):** the only place generated code runs. No network, no root, CPU, memory and time limits.

**Owner:** Lane D.
**Endpoint:** `POST /v1/code`, `CodeTask` to `CodeResult` (`routes.CODE`). W8 is the caller.

## Files

- `solve.py`: the online flow. `generate.py`, `runner.py`, `excel.py`, `check.py`: its parts.
- `job.py`, `listings.py`: offline.
- `sandbox/runner.py`, `sandbox/Dockerfile`: the sandbox image.

## Start here

1. `check.compare` and `excel.evaluate`, pure and easy to test.
2. `sandbox/runner.py`, the security-critical part. Get it reviewed.
3. `runner.SandboxRunner`, `generate.write_code`, then `solve.solve`.

## Test

```bash
uv run --package chatbot-w3-code pytest workers/w3_code/tests
```
