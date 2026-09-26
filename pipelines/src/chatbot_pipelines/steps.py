"""Run one worker step in its own container. Stub owned by Lane A.

Purpose
One worker, one package, two entrypoints. Online the worker runs inside the api process. Offline
the pipeline never imports worker code. It starts the worker job command in its own container from
the app image, the same image the api service runs, with Dagster Pipes. Every step still gets its
own container, so its logs, duration and resources are measured apart.

What to build
WORKER_COMMANDS maps each worker to its job command. run_step starts APP_IMAGE with that command
using PipesDockerClient locally and the ECS Pipes client on AWS, passes run id and document
version, streams logs and fails the Dagster step when the command fails. Record the image digest
for the ingestion run lineage.

How to test
Replace the image with a tiny image that echoes its arguments and assert the command line.
"""

APP_IMAGE = "ai-chatbot/api"

WORKER_COMMANDS: dict[str, str] = {
    "w1_ingest": "chatbot-w1-ingest-job",
    "w2_vision": "chatbot-w2-vision-job",
    "w3_code": "chatbot-w3-code-job",
    "w4_math": "chatbot-w4-math-job",
    "w5_clean": "chatbot-w5-clean-job",
    "w6_embed": "chatbot-w6-embed-job",
    "w7_deepsearch": "chatbot-w7-enrichment-job",
}


def run_step(worker: str, run_id: str, doc_version: str) -> str:
    """Run the job of one worker and return the image digest that ran."""
    raise NotImplementedError("worker steps are not written yet")
