"""Errors raised by the platform."""


class NotFoundError(LookupError):
    pass


class VersioningError(ValueError):
    """A corpus version operation would break the versioning rules."""
