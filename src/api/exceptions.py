"""
Custom exceptions for Suno API Client
"""


class SunoAPIError(Exception):
    """Base exception for Suno API errors"""
    
    def __init__(self, message: str, code: int = None):
        self.message = message
        self.code = code
        super().__init__(self.message)


class AuthenticationError(SunoAPIError):
    """Raised when API authentication fails (401)"""
    pass


class InsufficientCreditsError(SunoAPIError):
    """Raised when account has insufficient credits (429)"""
    pass


class RateLimitError(SunoAPIError):
    """Raised when rate limit is exceeded (405, 430)"""
    pass


class TaskFailedError(SunoAPIError):
    """Raised when a generation task fails"""
    pass


class TaskTimeoutError(SunoAPIError):
    """Raised when waiting for task completion times out"""
    pass


class InvalidParametersError(SunoAPIError):
    """Raised when invalid parameters are provided (400)"""
    pass
