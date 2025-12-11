"""
NPC Generator Models
"""

from pydantic import BaseModel, Field
from typing import Optional, List


class NPCRequest(BaseModel):
    """Request model for NPC generation"""
    mode: str = Field(
        'quick',
        description="Generation mode: 'quick' or 'detailed'"
    )
    race: Optional[str] = Field(
        None,
        description="Specific race (e.g., 'elf', 'dwarf', 'human'). Leave empty for random."
    )
    role: Optional[str] = Field(
        None,
        description="NPC role (e.g., 'shopkeeper', 'guard', 'noble', 'villain'). Leave empty for random."
    )
    level: Optional[int] = Field(
        None,
        description="Character level (1-20). Leave empty for level appropriate to role.",
        ge=1,
        le=20
    )
    personality_trait: Optional[str] = Field(
        None,
        description="Specific personality trait to emphasize"
    )


class NPCResponse(BaseModel):
    """Response model for generated NPC"""
    name: str
    race: str
    role: str
    age: str
    appearance: str
    personality: str
    quirk: str
    voice: str

    # Detailed mode fields
    background: Optional[str] = None
    motivation: Optional[str] = None
    secret: Optional[str] = None
    stats: Optional[dict] = None
    skills: Optional[List[str]] = None
    equipment: Optional[List[str]] = None

    mode: str
    tokens_used: int
