"""Register and promote adapters with MLflow. Stub owned by Lane D.

What to build
register logs the adapter with lineage tags for dataset version and corpus version, plus the test
split and RAGAs results against the current production model. promote is manual, it marks the
version for serving and the LLM server loads the adapter. Rollback promotes the previous version.

How to test
Use a local file based MLflow tracking folder in the test.
"""


def register(adapter_path: str, dataset_version: str, corpus_version: int) -> str:
    raise NotImplementedError("model registration is not written yet")


def promote(model_version: str) -> None:
    raise NotImplementedError("promotion is not written yet")
