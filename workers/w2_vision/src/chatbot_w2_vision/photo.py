"""Read a student photo of a problem set, a chart or a handwritten formula. Stub owned by Lane B.

Purpose
Appendix A.4 asks W2 to process photographed problem sets. This is the answer time path, so it
must stay fast. Measure it on CPU because it counts toward latency. It runs inside the api
process, so await the vision model and keep image decoding in a worker thread.

Input
A VisionRequest whose attachment points to the uploads bucket.

Output
A VisionResult with the transcribed text, formulas as LaTeX, detected_kind and a confidence.
Use detected_kind values problem_set, chart, handwritten_formula or other. A low confidence tells
the orchestrator to ask the student to retype the question.

What to build
Load the bytes with the platform object store, send them to the vision language model with a
transcription prompt, parse formulas into the latex list. Never log the image or its text.

How to test
Fake the model with an httpx MockTransport and the store with make_test_platform.
"""

from chatbot_contracts.query import VisionRequest, VisionResult


async def read_photo(request: VisionRequest) -> VisionResult:
    raise NotImplementedError("reading student photos is not written yet")
