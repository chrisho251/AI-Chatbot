"""Pseudonymize student ids. Stub owned by Lane C with the security part of Lane A.

Purpose
pseudo_user is an HMAC SHA256 of the student id with a key held in Vault. Nothing after the gateway
ever sees the real id. Destroying an old key epoch makes its pseudonyms unlinkable.

What to build
Call the Vault Transit HMAC endpoint with hvac for the configured key, return the hex digest.
If Vault is unreachable raise an error that the ask flow turns into 503, never fall back to the
raw id.

How to test
Fake Vault with a MockTransport and assert the same id always gives the same pseudonym.
"""


async def pseudonymize(student_id: str) -> str:
    raise NotImplementedError("pseudonymization is not written yet")
