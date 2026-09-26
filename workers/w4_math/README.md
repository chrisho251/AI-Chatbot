# W4 math

Worker-math from Appendix A.4. Two roles in one package:

- **Offline (ingest):** turns equations into normalized LaTeX.
- **Online (answer time):** computes and verifies values for W8, with SymPy and a catalogue of statistical operations.

**Owner:** Lane D.
**Endpoint:** `POST /v1/calc`, `CalcCheck` to `CalcResult` (`routes.CALC`). W8 is the caller.

## Files

- `calc.py`, `catalogue.py`: online.
- `job.py`, `latex.py`: offline.

## Start here

`catalogue.OPERATIONS` and `calc.check` first. They are pure functions and give W8 real numbers early.

## Test

```bash
uv run --package chatbot-w4-math pytest workers/w4_math/tests
```
