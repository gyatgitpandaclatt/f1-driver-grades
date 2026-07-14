class UpstreamAPIError(Exception):
    """Raised when the external F1 data provider is unreachable or returns bad data."""


class NoRaceDataError(Exception):
    """Raised when a season has zero completed races yet (e.g. preseason)."""
