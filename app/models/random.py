"""
Random Generator Models
"""

from pydantic import BaseModel, Field
from typing import Optional, List


class RandomRequest(BaseModel):
    """Request model for random generation"""
    generator_type: str = Field(
        ...,
        description="Type: 'name', 'loot', 'encounter', 'plot_hook', 'tavern_name', 'quest', 'rumor', 'trap'"
    )
    context: Optional[str] = Field(
        None,
        description="Additional context (e.g., race for names, CR for encounters, location for loot)"
    )
    count: int = Field(
        1,
        description="Number of items to generate (1-10)",
        ge=1,
        le=10
    )


class RandomResponse(BaseModel):
    """Response model for random generation"""
    generator_type: str
    context: Optional[str] = None
    results: List[str]
    tokens_used: int
