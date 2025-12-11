"""
Pydantic models for chat requests and responses
These define the structure of data going in and out of the API
"""

from pydantic import BaseModel, Field
from typing import Optional


class ChatRequest(BaseModel):
    """
    What the user sends when they ask a question
    """
    message: str = Field(
        ...,
        description="The user's question or request",
        min_length=1,
        max_length=4000
    )
    system_prompt: Optional[str] = Field(
        None,
        description="Optional custom system prompt for this request"
    )


class ChatResponse(BaseModel):
    """
    What the API sends back with Claude's answer
    """
    response: str = Field(..., description="Claude's response to the user")
    tokens_used: Optional[int] = Field(None, description="Number of tokens used in this request")
    model: str = Field(..., description="Which Claude model was used")
