"""
Data models for Suno API
"""
from dataclasses import dataclass, field
from typing import Optional, List
from enum import Enum


class Model(str, Enum):
    """Available Suno AI models"""
    V3_5 = "V3_5"      # Creative diversity, up to 4 min
    V4 = "V4"          # Best audio quality, up to 4 min
    V4_5 = "V4_5"      # Advanced features, up to 8 min
    V4_5PLUS = "V4_5PLUS"  # Richer sound, up to 8 min
    V5 = "V5"          # Fastest, superior musicality, up to 8 min


class TaskStatusEnum(str, Enum):
    """Task status values"""
    PENDING = "PENDING"
    GENERATING = "GENERATING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"


class VocalGender(str, Enum):
    """Vocal gender options"""
    MALE = "m"
    FEMALE = "f"


class SeparationType(str, Enum):
    """Vocal separation types"""
    SEPARATE_VOCAL = "separate_vocal"  # 2 stems - vocals + instrumental
    SPLIT_STEM = "split_stem"          # Up to 12 stems


@dataclass
class MusicTrack:
    """Represents a generated music track"""
    id: str
    title: str
    audio_url: str
    duration: float
    tags: str = ""
    image_url: str = ""
    video_url: str = ""
    
    @classmethod
    def from_dict(cls, data: dict) -> "MusicTrack":
        return cls(
            id=data.get("id", ""),
            title=data.get("title", ""),
            audio_url=data.get("audio_url", ""),
            duration=data.get("duration", 0.0),
            tags=data.get("tags", ""),
            image_url=data.get("image_url", ""),
            video_url=data.get("video_url", "")
        )


@dataclass
class LyricsResult:
    """Represents generated lyrics"""
    id: str
    text: str
    title: str = ""
    
    @classmethod
    def from_dict(cls, data: dict) -> "LyricsResult":
        return cls(
            id=data.get("id", ""),
            text=data.get("text", ""),
            title=data.get("title", "")
        )


@dataclass
class TaskStatus:
    """Represents the status of a generation task"""
    task_id: str
    status: TaskStatusEnum
    tracks: List[MusicTrack] = field(default_factory=list)
    lyrics: List[LyricsResult] = field(default_factory=list)
    error_message: str = ""
    
    @property
    def is_complete(self) -> bool:
        return self.status == TaskStatusEnum.SUCCESS
    
    @property
    def is_failed(self) -> bool:
        return self.status == TaskStatusEnum.FAILED
    
    @property
    def is_pending(self) -> bool:
        return self.status in [TaskStatusEnum.PENDING, TaskStatusEnum.GENERATING]


@dataclass
class VocalSeparationResult:
    """Represents vocal separation results"""
    task_id: str
    audio_id: str
    original_url: str = ""
    vocal_url: str = ""
    instrumental_url: str = ""
    stems: dict = field(default_factory=dict)  # For split_stem type


@dataclass 
class GenerationRequest:
    """Request parameters for music generation"""
    prompt: str
    model: Model = Model.V4_5
    custom_mode: bool = False
    instrumental: bool = False
    style: Optional[str] = None
    title: Optional[str] = None
    persona_id: Optional[str] = None
    negative_tags: Optional[str] = None
    vocal_gender: Optional[VocalGender] = None
    style_weight: Optional[float] = None
    weirdness_constraint: Optional[float] = None
    audio_weight: Optional[float] = None
    
    def to_dict(self) -> dict:
        """Convert to API request dictionary"""
        data = {
            "prompt": self.prompt,
            "model": self.model.value if isinstance(self.model, Model) else self.model,
            "customMode": self.custom_mode,
            "instrumental": self.instrumental,
        }
        
        if self.style:
            data["style"] = self.style
        if self.title:
            data["title"] = self.title
        if self.persona_id:
            data["personaId"] = self.persona_id
        if self.negative_tags:
            data["negativeTags"] = self.negative_tags
        if self.vocal_gender:
            data["vocalGender"] = self.vocal_gender.value if isinstance(self.vocal_gender, VocalGender) else self.vocal_gender
        if self.style_weight is not None:
            data["styleWeight"] = self.style_weight
        if self.weirdness_constraint is not None:
            data["weirdnessConstraint"] = self.weirdness_constraint
        if self.audio_weight is not None:
            data["audioWeight"] = self.audio_weight
            
        return data
