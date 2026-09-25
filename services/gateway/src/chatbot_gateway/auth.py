"""OIDC token validation and roles. Stub owned by Lane C.

Purpose
Validate the bearer token issued by Keycloak locally or Cognito on AWS, and return who is calling.
Roles are student, sme, expert, data_engineer, ml_engineer, ops and auditor.

What to build
Fetch the issuer JWKS once and cache it, verify signature, issuer, audience and expiry with Authlib,
read the subject and the realm roles. Raise HTTPException 401 or 403.

How to test
Sign tokens with a key generated in the test and serve the JWKS through an httpx MockTransport.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Principal:
    subject: str
    roles: frozenset[str]


async def authenticate(authorization: str, required_role: str = "student") -> Principal:
    raise NotImplementedError("authentication is not written yet")
