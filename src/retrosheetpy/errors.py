"""Structured errors raised by retrosheetpy."""


class RetrosheetError(Exception):
    """Base class for all retrosheetpy errors."""


class IntegrityError(RetrosheetError):
    """A cached file's bytes no longer match its recorded SHA-256."""


class InvalidArchiveError(RetrosheetError):
    """A download or file is not a valid zip archive."""


class UnsafeArchiveMemberError(RetrosheetError):
    """A zip member name would escape the archive (absolute path or '..')."""


class ArchiveTooLargeError(InvalidArchiveError):
    """A zip holds more members or more data than any Retrosheet archive should (zip-bomb guard)."""


class ToolError(RetrosheetError):
    """A chadwickpy tool run on a season exited with an error."""
