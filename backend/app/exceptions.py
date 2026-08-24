class UpstreamAPIError(Exception):
    """Raised when the external F1 data provider is unreachable or returns bad data."""


class NoRaceDataError(Exception):
    """Raised when a season has zero completed races yet (e.g. preseason)."""


class RaceSessionNotAvailableError(Exception):
    """Raised when the data provider has no results yet for the latest completed round."""


class NarrativeGenerationError(Exception):
    """Raised when the Claude narrative call fails or is declined."""


class UpstreamRateLimitedError(UpstreamAPIError):
    """Raised when the data provider rate-limits us (HTTP 429).

    A subclass of UpstreamAPIError so existing `except UpstreamAPIError`
    call sites still catch it, but handled separately at the API edge: this
    is a "busy, try again shortly" (503 + Retry-After), not a bad gateway.
    """

    def __init__(self, message: str, retry_after: int):
        super().__init__(message)
        self.retry_after = retry_after
