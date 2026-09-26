"""Pseudonymize student ids. Stub owned by Lane C with the security part of Lane A.

Purpose
pseudo_user is an HMAC SHA256 of the student id with a key from the KeyService. Nothing after the
gateway ever sees the real id. Destroying an old key epoch makes its pseudonyms unlinkable.

What to build
Call KeyService.pseudonym from chatbot_common.keys, with FileKeyService locally and KMS on AWS.
If the keys are unavailable raise an error that the ask flow turns into 503, never fall back to
the raw id.

How to test
Use FileKeyService with a key file in tmp_path and assert the same id always gives the same
pseudonym, and that a missing key file gives 503.
"""


async def pseudonymize(student_id: str) -> str:
    raise NotImplementedError("pseudonymization is not written yet")
