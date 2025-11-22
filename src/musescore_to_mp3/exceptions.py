"""Custom exceptions for the musescore-to-mp3 package."""


class MuseScoreConverterError(Exception):
    """Base exception for MuseScore converter errors."""
    pass


class MuseScoreNotFoundError(MuseScoreConverterError):
    """Raised when MuseScore executable is not found."""
    pass


class MuseScoreExecutionError(MuseScoreConverterError):
    """Raised when MuseScore execution fails."""
    pass


class InvalidMSCZFileError(MuseScoreConverterError):
    """Raised when the .mscz file is invalid or corrupted."""
    pass


class VoiceNotFoundError(MuseScoreConverterError):
    """Raised when the specified voice group is not found."""
    pass


class XMLModificationError(MuseScoreConverterError):
    """Raised when XML modification fails."""
    pass
