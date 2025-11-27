"""
Suno API module
"""
from .client import SunoAPI
from .models import GenerationRequest, TaskStatus, MusicTrack
from .exceptions import SunoAPIError, AuthenticationError, InsufficientCreditsError

__all__ = [
    "SunoAPI",
    "GenerationRequest",
    "TaskStatus", 
    "MusicTrack",
    "SunoAPIError",
    "AuthenticationError",
    "InsufficientCreditsError"
]
