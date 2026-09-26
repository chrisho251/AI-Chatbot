# Fine-tuning

Dataset build, SME approval gate, QLoRA training, evaluation and registry, following [ARCHITECTURE.md](../../docs/architecture/ARCHITECTURE.md), section 7, and Appendix A.5.

**Owner:** Lane D.
**Writes:** `ft.datasets`, `ft.items`, one Parquet export per dataset version in the `exports` bucket, and MLflow models.
**Hardware:** training needs an NVIDIA GPU. Everything else runs on any machine.
**Phase:** optional and later. Start only when RAGAs shows that generation, not retrieval, limits answer quality. MLflow runs in the `finetune` compose profile.

## Files

- `dataset.py`, `split.py`: build and freeze a dataset version.
- `approval.py`: the SME gate.
- `train.py`: QLoRA.
- `registry.py`: MLflow and promotion.

## Start here

1. Write the dataset methodology document for the M3 milestone.
2. `split.assign` and `dataset.build` on a small set of SME pairs.
3. `approval`, then `train` with a dry run on a tiny model.

## Test

```bash
uv run --package chatbot-finetune pytest ml/finetune/tests
```
