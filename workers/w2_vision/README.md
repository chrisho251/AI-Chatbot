# W2 vision

Worker-vision from Appendix A.4. Two roles in one package:

- **Offline (ingest):** OCR for scans and image tables, captions and alt text for figures.
- **Online (answer time):** reads a student photo of a problem set, chart or handwritten formula.

**Owner:** Lane B.
**Offline reads:** `ingest.regions` of kinds figure, scan and table. **Writes:** `ingest.extracted_regions`.
**Online endpoint:** `POST /v1/vision`, `VisionRequest` to `VisionResult` (see `chatbot_contracts.routes.VISION`).

## Files

- `serve.py`: `HANDLERS`, called in process by the api service, and `app`, the same handler over HTTP. Run it alone with `uvicorn chatbot_w2_vision.serve:app`.
- `job.py`: offline entrypoint.
- `ocr.py`, `captions.py`: offline extraction.
- `photo.py`: online photo reading.

## Start here

1. `ocr.ocr_region` and `job.run`, tested with `make_test_platform` and a fixture image.
2. `photo.read_photo` with a faked vision model (httpx `MockTransport`).
3. `captions.caption_figure` last. It only improves search over figures.

## Test

```bash
uv run --package chatbot-w2-vision pytest workers/w2_vision/tests
```
