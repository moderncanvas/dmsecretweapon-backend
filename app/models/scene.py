"""
Scene Generator Models
"""

from pydantic import BaseModel, Field
from typing import Optional, List


class SceneRequest(BaseModel):
    """Request model for scene generation"""
    scene_type: str = Field(
        ...,
        description="Type of scene: 'dungeon', 'tavern', 'wilderness', 'city', 'temple', 'combat', 'mystery', 'social'"
    )
    mood: Optional[str] = Field(
        None,
        description="Desired mood: 'ominous', 'cheerful', 'tense', 'peaceful', 'mysterious', 'action-packed'"
    )
    setting_details: Optional[str] = Field(
        None,
        description="Additional details about the setting (e.g., 'abandoned', 'crowded', 'ancient')"
    )
    include_sensory: bool = Field(
        True,
        description="Include sensory details (sounds, smells, textures)"
    )
    length: str = Field(
        'medium',
        description="Scene length: 'short' (1 paragraph), 'medium' (2-3 paragraphs), 'long' (4-5 paragraphs)"
    )


class SceneResponse(BaseModel):
    """Response model for generated scene"""
    scene_type: str
    mood: str
    description: str
    read_aloud_text: str
    dm_notes: Optional[str] = None
    suggested_encounters: Optional[List[str]] = None
    points_of_interest: Optional[List[str]] = None
    tokens_used: int
