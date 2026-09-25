"""Deterministic train, validation and test split. Stub owned by Lane D.

What to build
80, 10 and 10 percent by a hash of the item id, stratified by course and topic so every split sees
every topic. The same item always lands in the same split, which keeps the dataset reproducible.

How to test
Assign 10000 fake ids and check the shares within one percent, and that assignment is stable.
"""


def assign(item_id: str, course_code: str, topic: str) -> str:
    """Return train, validation or test."""
    raise NotImplementedError("splitting is not written yet")
