"""
Chat API endpoint - handles AI conversations with Claude
"""

from fastapi import APIRouter, HTTPException
from anthropic import Anthropic
import os

from app.models.chat import ChatRequest, ChatResponse
from app.services.srd_service import get_srd_service

# Create router for chat endpoints
router = APIRouter()

# Initialize Anthropic client
# This reads your API key from the environment variable we set in .env
client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

# Default system prompt for D&D assistance
DEFAULT_SYSTEM_PROMPT = """You are an expert Dungeon Master assistant for D&D 5th Edition. You help DMs with:

- Rules questions and clarifications
- NPC generation and characterization
- Scene descriptions and atmospheric storytelling
- Combat and encounter suggestions
- Plot hooks and story ideas
- Quick reference for spells, conditions, and monster stats

Keep responses concise but helpful. When describing stat blocks or rules, format them clearly.
If you're not sure about a rule, acknowledge it and suggest how to handle it."""


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Send a message to Claude and get a response

    This is your main AI assistant endpoint!
    """
    try:
        # Determine which system prompt to use
        system_prompt = request.system_prompt or DEFAULT_SYSTEM_PROMPT

        # Search SRD for relevant context
        srd = get_srd_service()
        srd_results = srd.search(request.message, collection_name='all', n_results=3)

        # Build context from SRD results
        srd_context = ""
        if srd_results:
            srd_context = "\n\n=== RELEVANT D&D 5e SRD INFORMATION ===\n"
            for result in srd_results:
                srd_context += f"\n**{result['metadata'].get('name', 'Unknown')}** ({result['metadata'].get('type', 'unknown')})\n"
                srd_context += f"{result['text']}\n"
            srd_context += "\n=== END SRD INFORMATION ===\n"

        # Combine user message with SRD context
        full_message = request.message
        if srd_context:
            full_message = f"{request.message}\n{srd_context}\n\nPlease use the SRD information above to provide an accurate answer."

        # Call Claude API
        message = client.messages.create(
            model="claude-sonnet-4-20250514",  # Latest Claude Sonnet model
            max_tokens=2048,
            system=system_prompt,
            messages=[
                {
                    "role": "user",
                    "content": full_message
                }
            ]
        )

        # Extract the response text
        response_text = message.content[0].text

        # Return formatted response
        return ChatResponse(
            response=response_text,
            tokens_used=message.usage.input_tokens + message.usage.output_tokens,
            model=message.model
        )

    except Exception as e:
        # If something goes wrong, return a helpful error
        raise HTTPException(
            status_code=500,
            detail=f"Error communicating with Claude: {str(e)}"
        )


@router.get("/chat/test")
async def test_chat():
    """
    Quick test endpoint to verify Claude API is working
    """
    try:
        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=100,
            messages=[
                {
                    "role": "user",
                    "content": "Say 'Hello, Dungeon Master!' in a friendly way."
                }
            ]
        )

        return {
            "status": "success",
            "message": message.content[0].text,
            "model": message.model
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Claude API test failed: {str(e)}"
        )
