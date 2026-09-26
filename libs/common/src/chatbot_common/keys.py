"""Keys for pseudonyms and for encrypting student free text. Stub owned by Lane A, security.

Purpose
The gateway turns a student id into pseudo_user with an HMAC SHA256, and services encrypt the
question and answer text before they store it. Keys come in epochs. Destroying an old epoch makes
its pseudonyms unlinkable and its ciphertext unreadable, which is how retention shreds student data.
Everything goes through the KeyService protocol, so the local key file and KMS on AWS swap freely.

What to build
FileKeyService reads the JSON key file at CHATBOT_KEY_FILE. It holds the current epoch and one
random 32 byte key per epoch. pseudonym returns the epoch and the hex HMAC of the value. encrypt
uses AES GCM from the cryptography package with a fresh nonce and returns epoch, nonce and
ciphertext in one base64 string, decrypt reverses it. A missing file or epoch raises
KeyServiceError. Callers fail closed and never fall back to the raw id or to plain text.
Add a small script in scripts that writes a new key file, and a command that drops an epoch.
A KMS adapter with the same protocol replaces this class on AWS.

How to test
Write a key file in tmp_path. The same id always gives the same pseudonym, decrypt reverses
encrypt, and ciphertext of a dropped epoch raises KeyServiceError.
"""

from pathlib import Path
from typing import Protocol


class KeyServiceError(RuntimeError):
    """Keys are unavailable. The caller must refuse the request instead of storing raw data."""


class KeyService(Protocol):
    def pseudonym(self, value: str) -> str: ...

    def encrypt(self, plaintext: str) -> str: ...

    def decrypt(self, token: str) -> str: ...


class FileKeyService:
    """Local adapter over the key file mounted into the api container."""

    def __init__(self, path: Path) -> None:
        self.path = path

    def pseudonym(self, value: str) -> str:
        raise NotImplementedError("the key file adapter is not written yet")

    def encrypt(self, plaintext: str) -> str:
        raise NotImplementedError("the key file adapter is not written yet")

    def decrypt(self, token: str) -> str:
        raise NotImplementedError("the key file adapter is not written yet")
