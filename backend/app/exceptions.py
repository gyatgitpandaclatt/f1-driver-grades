class UpstreamAPIError(Exception):
    """Raised when the external F1 data provider is unreachable or returns bad data."""


class NoRaceDataError(Exception):
    """Raised when a season has zero completed races yet (e.g. preseason)."""


class RaceSessionNotAvailableError(Exception):
    """Raised when the data provider has no results yet for the latest completed round."""


class NarrativeGenerationError(Exception):
    """Raised when the Claude narrative call fails or is declined."""
