"""Run one worker step in its own image. Stub owned by Lane A.

Purpose
One worker, one image. The pipeline never imports worker code. It starts the worker CLI in the
worker image with Dagster Pipes, so each lane ships its worker on its own.

What to build
WORKER_IMAGES maps each worker to its image and job command, for example the W1 image with the
chatbot w1 ingest job command. run_step starts it with PipesDockerClient locally and with the ECS
Pipes client on AWS, passes run id and document version, streams logs and fails the Dagster step
when the command fails. Record the image digest for the ingestion run lineage.

How to test
Replace the images with a tiny image that echoes its arguments and assert the command line.
"""

WORKER_IMAGES: dict[str, str] = {
    "w1_ingest": "ai-chatbot/w1-ingest",
    "w2_vision": "ai-chatbot/w2-vision",
    "w3_code": "ai-chatbot/w3-code",
    "w4_math": "ai-chatbot/w4-math",
    "w5_clean": "ai-chatbot/w5-clean",
    "w6_embed": "ai-chatbot/w6-embed",
    "w7_deepsearch": "ai-chatbot/w7-deepsearch",
}


def run_step(worker: str, run_id: str, doc_version: str) -> str:
    """Run the job of one worker and return the image digest that ran."""
    raise NotImplementedError("worker steps are not written yet")
