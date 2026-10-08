class UpstreamAPIError(Exception):
    """Raised when the external F1 data provider is unreachable or returns bad data."""


class NoRaceDataError(Exception):
    """Raised when a season has zero completed races yet (e.g. preseason)."""


class RaceSessionNotAvailableError(Exception):
    """Raised when the data provider has no results yet for the latest completed round."""


class NarrativeGenerationError(Exception):
    """Raised when the narrative call fails transiently.

    The caller is invited to retry: the API was unreachable, overloaded, or
    rate limited.
    """


class NarrativeUnavailableError(NarrativeGenerationError):
    """Raised when the narrative call fails for a reason retrying cannot fix.

    A rejected or missing API key, an unknown model, a request the API
    refuses outright. These need someone to change an account or a
    configuration; telling a visitor to "try again shortly" is simply false,
    and the frontend's auto-retry would hammer a call that cannot succeed.

    Subclasses NarrativeGenerationError so existing handling still catches it.
    """


class UpstreamRateLimitedError(UpstreamAPIError):
    """Raised when the data provider rate-limits us (HTTP 429).

    A subclass of UpstreamAPIError so existing `except UpstreamAPIError`
    call sites still catch it, but handled separately at the API edge: this
    is a "busy, try again shortly" (503 + Retry-After), not a bad gateway.
    """

    def __init__(self, message: str, retry_after: int):
        super().__init__(message)
        self.retry_after = retry_after
