"""Store a student attachment. Stub owned by Lane C.

Purpose
Photos and data files go to the uploads bucket and the ops.uploads table. They are student data,
so they are encrypted, have the shortest TTL and are never used for training.

What to build
Check media type and size against GatewaySettings, compute sha256, write to the uploads bucket under
the date and request id key from ARCHITECTURE.md section 4.1, insert the ops.uploads row, return an
Attachment.

How to test
Use make_test_platform from chatbot_platform.testing and assert the object and the row exist.
"""

from fastapi import UploadFile

from chatbot_contracts.query import Attachment


async def store_attachment(request_id: str, file: UploadFile) -> Attachment:
    raise NotImplementedError("uploads are not written yet")
