"""
Suno API Client - Main API wrapper
"""
import time
import requests
from pathlib import Path
from typing import Optional, Union

from .models import (
    Model, TaskStatus, TaskStatusEnum, MusicTrack, LyricsResult,
    VocalSeparationResult, GenerationRequest, SeparationType, VocalGender
)
from .exceptions import (
    SunoAPIError, AuthenticationError, InsufficientCreditsError,
    RateLimitError, TaskFailedError, TaskTimeoutError, InvalidParametersError
)


class SunoAPI:
    """
    Suno AI Music Generation API Client
    
    Usage:
        api = SunoAPI(api_key="your_api_key")
        task_id = api.generate_music("upbeat jazz song")
        result = api.wait_for_completion(task_id)
    """
    
    BASE_URL = "https://api.sunoapi.org/api/v1"
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        })
    
    def _handle_response(self, response: requests.Response) -> dict:
        """Handle API response and raise appropriate exceptions"""
        try:
            data = response.json()
        except ValueError:
            raise SunoAPIError(f"Invalid JSON response: {response.text}")
        
        code = data.get("code", response.status_code)
        msg = data.get("msg", "Unknown error")
        
        if code == 200:
            return data
        elif code == 400:
            raise InvalidParametersError(msg, code)
        elif code == 401:
            raise AuthenticationError(msg, code)
        elif code == 405 or code == 430:
            raise RateLimitError(msg, code)
        elif code == 429:
            raise InsufficientCreditsError(msg, code)
        else:
            raise SunoAPIError(msg, code)
    
    # ==================== Account ====================
    
    def get_credits(self) -> int:
        """Get remaining credits balance"""
        response = self.session.get(f"{self.BASE_URL}/generate/credit")
        data = self._handle_response(response)
        return data.get("data", 0)
    
    # ==================== Music Generation ====================
    
    def generate_music(
        self,
        prompt: str,
        model: Union[Model, str] = Model.V4_5,
        custom_mode: bool = False,
        instrumental: bool = False,
        style: Optional[str] = None,
        title: Optional[str] = None,
        persona_id: Optional[str] = None,
        negative_tags: Optional[str] = None,
        vocal_gender: Optional[Union[VocalGender, str]] = None,
        style_weight: Optional[float] = None,
        weirdness_constraint: Optional[float] = None,
        audio_weight: Optional[float] = None
    ) -> str:
        """
        Generate music from text description.
        Returns task ID for tracking.
        
        Args:
            prompt: Text description of the music (or lyrics in custom mode)
            model: AI model version (V3_5, V4, V4_5, V4_5PLUS, V5)
            custom_mode: Enable custom parameters (requires style & title)
            instrumental: Generate instrumental only (no vocals)
            style: Music genre/style (required in custom mode)
            title: Song title (required in custom mode)
            persona_id: Apply specific persona style
            negative_tags: Styles to exclude
            vocal_gender: 'm' for male, 'f' for female
            style_weight: Style influence (0.0-1.0)
            weirdness_constraint: Creative deviation (0.0-1.0)
            audio_weight: Audio influence (0.0-1.0)
        
        Returns:
            Task ID string
        """
        payload = {
            "prompt": prompt,
            "model": model.value if isinstance(model, Model) else model,
            "customMode": custom_mode,
            "instrumental": instrumental,
        }
        
        if style:
            payload["style"] = style
        if title:
            payload["title"] = title
        if persona_id:
            payload["personaId"] = persona_id
        if negative_tags:
            payload["negativeTags"] = negative_tags
        if vocal_gender:
            payload["vocalGender"] = vocal_gender.value if isinstance(vocal_gender, VocalGender) else vocal_gender
        if style_weight is not None:
            payload["styleWeight"] = style_weight
        if weirdness_constraint is not None:
            payload["weirdnessConstraint"] = weirdness_constraint
        if audio_weight is not None:
            payload["audioWeight"] = audio_weight
        
        response = self.session.post(f"{self.BASE_URL}/generate", json=payload)
        data = self._handle_response(response)
        return data["data"]["taskId"]
    
    # ==================== Lyrics Generation ====================
    
    def generate_lyrics(self, prompt: str) -> str:
        """
        Generate lyrics from text description.
        
        Args:
            prompt: Description of desired lyrics (max 200 words)
        
        Returns:
            Task ID string
        """
        payload = {"prompt": prompt}
        
        response = self.session.post(f"{self.BASE_URL}/lyrics", json=payload)
        data = self._handle_response(response)
        return data["data"]["taskId"]
    
    # ==================== Extend Music ====================
    
    def extend_music(
        self,
        audio_id: str,
        model: Union[Model, str] = Model.V4_5,
        default_param_flag: bool = False,
        continue_at: Optional[float] = None,
        prompt: Optional[str] = None,
        style: Optional[str] = None,
        title: Optional[str] = None,
        persona_id: Optional[str] = None,
        negative_tags: Optional[str] = None,
        vocal_gender: Optional[Union[VocalGender, str]] = None,
        style_weight: Optional[float] = None,
        weirdness_constraint: Optional[float] = None,
        audio_weight: Optional[float] = None
    ) -> str:
        """
        Extend an existing music track.
        
        Args:
            audio_id: ID of the track to extend
            model: Must match the source audio's model
            default_param_flag: True = custom params, False = use original
            continue_at: Time in seconds to start extension
            prompt: Description of how to extend (required if default_param_flag=True)
            style: Music style (required if default_param_flag=True)
            title: Song title (required if default_param_flag=True)
        
        Returns:
            Task ID string
        """
        payload = {
            "audioId": audio_id,
            "model": model.value if isinstance(model, Model) else model,
            "defaultParamFlag": default_param_flag,
        }
        
        if continue_at is not None:
            payload["continueAt"] = continue_at
        if prompt:
            payload["prompt"] = prompt
        if style:
            payload["style"] = style
        if title:
            payload["title"] = title
        if persona_id:
            payload["personaId"] = persona_id
        if negative_tags:
            payload["negativeTags"] = negative_tags
        if vocal_gender:
            payload["vocalGender"] = vocal_gender.value if isinstance(vocal_gender, VocalGender) else vocal_gender
        if style_weight is not None:
            payload["styleWeight"] = style_weight
        if weirdness_constraint is not None:
            payload["weirdnessConstraint"] = weirdness_constraint
        if audio_weight is not None:
            payload["audioWeight"] = audio_weight
        
        response = self.session.post(f"{self.BASE_URL}/generate/extend", json=payload)
        data = self._handle_response(response)
        return data["data"]["taskId"]
    
    # ==================== Upload & Cover ====================
    
    def upload_and_cover(
        self,
        upload_url: str,
        model: Union[Model, str] = Model.V4_5,
        custom_mode: bool = False,
        instrumental: bool = False,
        prompt: Optional[str] = None,
        style: Optional[str] = None,
        title: Optional[str] = None,
        persona_id: Optional[str] = None,
        negative_tags: Optional[str] = None,
        vocal_gender: Optional[Union[VocalGender, str]] = None,
        style_weight: Optional[float] = None,
        weirdness_constraint: Optional[float] = None,
        audio_weight: Optional[float] = None
    ) -> str:
        """
        Transform uploaded audio with a new style while keeping melody.
        
        Args:
            upload_url: URL of the audio file to transform (max 8 min)
            model: AI model version
            custom_mode: Enable custom parameters
            instrumental: Generate instrumental only
            prompt: Description or lyrics
            style: New music style (required in custom mode)
            title: Song title (required in custom mode)
        
        Returns:
            Task ID string
        """
        payload = {
            "uploadUrl": upload_url,
            "model": model.value if isinstance(model, Model) else model,
            "customMode": custom_mode,
            "instrumental": instrumental,
        }
        
        if prompt:
            payload["prompt"] = prompt
        if style:
            payload["style"] = style
        if title:
            payload["title"] = title
        if persona_id:
            payload["personaId"] = persona_id
        if negative_tags:
            payload["negativeTags"] = negative_tags
        if vocal_gender:
            payload["vocalGender"] = vocal_gender.value if isinstance(vocal_gender, VocalGender) else vocal_gender
        if style_weight is not None:
            payload["styleWeight"] = style_weight
        if weirdness_constraint is not None:
            payload["weirdnessConstraint"] = weirdness_constraint
        if audio_weight is not None:
            payload["audioWeight"] = audio_weight
        
        response = self.session.post(f"{self.BASE_URL}/generate/upload-cover", json=payload)
        data = self._handle_response(response)
        return data["data"]["taskId"]
    
    # ==================== Vocal Separation ====================
    
    def separate_vocals(
        self,
        task_id: str,
        audio_id: str,
        separation_type: Union[SeparationType, str] = SeparationType.SEPARATE_VOCAL
    ) -> str:
        """
        Separate vocals from music.
        
        Args:
            task_id: Original music generation task ID
            audio_id: ID of the specific track
            separation_type: 'separate_vocal' (2 stems) or 'split_stem' (12 stems)
        
        Returns:
            Task ID string
        """
        payload = {
            "taskId": task_id,
            "audioId": audio_id,
            "type": separation_type.value if isinstance(separation_type, SeparationType) else separation_type
        }
        
        response = self.session.post(f"{self.BASE_URL}/vocal-removal/generate", json=payload)
        data = self._handle_response(response)
        return data["data"]["taskId"]
    
    # ==================== Video Generation ====================
    
    def create_video(
        self,
        task_id: str,
        audio_id: str,
        author: Optional[str] = None,
        domain_name: Optional[str] = None
    ) -> str:
        """
        Create an MP4 music video with visualizations.
        
        Args:
            task_id: Music generation task ID
            audio_id: ID of the specific track
            author: Artist name to display (max 50 chars)
            domain_name: Website for watermark (max 50 chars)
        
        Returns:
            Task ID string
        """
        payload = {
            "taskId": task_id,
            "audioId": audio_id,
        }
        
        if author:
            payload["author"] = author[:50]
        if domain_name:
            payload["domainName"] = domain_name[:50]
        
        response = self.session.post(f"{self.BASE_URL}/mp4/generate", json=payload)
        data = self._handle_response(response)
        return data["data"]["taskId"]
    
    # ==================== WAV Conversion ====================
    
    def convert_to_wav(self, task_id: str, audio_id: str) -> str:
        """
        Convert track to high-quality WAV format.
        
        Args:
            task_id: Music generation task ID
            audio_id: ID of the specific track
        
        Returns:
            Task ID string
        """
        payload = {
            "taskId": task_id,
            "audioId": audio_id,
        }
        
        response = self.session.post(f"{self.BASE_URL}/wav/generate", json=payload)
        data = self._handle_response(response)
        return data["data"]["taskId"]
    
    # ==================== Task Status ====================
    
    def get_task_status(self, task_id: str) -> TaskStatus:
        """
        Get the current status of a generation task.
        
        Args:
            task_id: The task ID to check
        
        Returns:
            TaskStatus object with current status and results
        """
        response = self.session.get(
            f"{self.BASE_URL}/generate/record-info",
            params={"taskId": task_id}
        )
        data = self._handle_response(response)
        task_data = data.get("data", {})
        
        status_str = task_data.get("status", "PENDING")
        try:
            status = TaskStatusEnum(status_str)
        except ValueError:
            status = TaskStatusEnum.PENDING
        
        tracks = []
        lyrics = []
        
        if "response" in task_data and task_data["response"]:
            response_data = task_data["response"].get("data", [])
            for item in response_data:
                if "audio_url" in item:
                    tracks.append(MusicTrack.from_dict(item))
                elif "text" in item:
                    lyrics.append(LyricsResult.from_dict(item))
        
        return TaskStatus(
            task_id=task_id,
            status=status,
            tracks=tracks,
            lyrics=lyrics,
            error_message=task_data.get("errorMessage", "")
        )
    
    # ==================== Utility Methods ====================
    
    def wait_for_completion(
        self,
        task_id: str,
        timeout: int = 600,
        poll_interval: int = 30,
        callback=None
    ) -> TaskStatus:
        """
        Wait for a task to complete, polling periodically.
        
        Args:
            task_id: The task ID to wait for
            timeout: Maximum wait time in seconds (default 10 min)
            poll_interval: Seconds between status checks (default 30s)
            callback: Optional function to call with status updates
        
        Returns:
            Final TaskStatus object
        
        Raises:
            TaskTimeoutError: If timeout is exceeded
            TaskFailedError: If task fails
        """
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            status = self.get_task_status(task_id)
            
            if callback:
                callback(status)
            
            if status.is_complete:
                return status
            elif status.is_failed:
                raise TaskFailedError(
                    f"Task failed: {status.error_message}",
                    code=None
                )
            
            time.sleep(poll_interval)
        
        raise TaskTimeoutError(f"Task {task_id} timed out after {timeout} seconds")
    
    def download_file(self, url: str, output_path: Union[str, Path]) -> Path:
        """
        Download a file from URL to local path.
        
        Args:
            url: URL of the file to download
            output_path: Local path to save the file
        
        Returns:
            Path to the downloaded file
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        response = requests.get(url, stream=True)
        response.raise_for_status()
        
        with open(output_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        return output_path
