"""SME approval gate for datasets. Stub owned by Lane D.

Purpose
Appendix A.5 requires SME approval before any training. Training refuses an unapproved version.

What to build
record_decision stores the approver, decision and comment on the ft.datasets row.
require_approved raises when the dataset version is not approved.

How to test
Training on a pending dataset raises, after approval it does not.
"""


def record_decision(dataset_version: str, approved: bool, by: str, comment: str | None) -> None:
    raise NotImplementedError("dataset approval is not written yet")


def require_approved(dataset_version: str) -> None:
    raise NotImplementedError("dataset approval is not written yet")
