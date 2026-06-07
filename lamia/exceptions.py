class LamiaError(Exception):
    """Base exception for the Lamia client."""


class AuthenticationError(LamiaError):
    """Raised when login or token refresh fails."""


class APIError(LamiaError):
    """Raised when the API returns an unexpected error response."""

    def __init__(self, status_code: int, detail: object) -> None:
        self.status_code = status_code
        self.detail = detail
        super().__init__(f"HTTP {status_code}: {detail}")
