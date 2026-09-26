"""Errors raised by the platform."""


class NotFoundError(LookupError):
    pass


class VersioningError(ValueError):
    """A knowledge base version operation would break the versioning rules."""
