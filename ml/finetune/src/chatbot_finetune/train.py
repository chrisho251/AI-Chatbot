"""QLoRA training of the serving base model. Stub owned by Lane D.

Purpose
Improve domain accuracy with a LoRA adapter on the small open weight base model.

What to build
require_approved first. Load the base model in 4 bit with bitsandbytes, train a LoRA adapter with
TRL SFTTrainer and PEFT on the train split, evaluate on validation. Record seed, config and the
container digest. Training needs an NVIDIA GPU, run it on the GPU host or a cloud notebook.

How to test
A dry run flag that builds everything and trains for one step on a tiny model.
"""


def train(dataset_version: str, base_model: str, dry_run: bool = False) -> str:
    """Train an adapter and return its local path."""
    raise NotImplementedError("training is not written yet")
