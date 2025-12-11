"""
NPC Generator API endpoint - creates D&D NPCs using Claude
"""

from fastapi import APIRouter, HTTPException
from anthropic import Anthropic
import os
import json

from app.models.npc import NPCRequest, NPCResponse

# Create router for NPC endpoints
router = APIRouter()

# Initialize Anthropic client
client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

# System prompts for different modes
QUICK_NPC_PROMPT = """You are an expert D&D 5e NPC generator. Generate memorable, practical NPCs that DMs can use immediately in their games.

For QUICK mode, provide:
- A fitting name
- Race
- Role/occupation
- Age description
- Brief appearance (1-2 sentences)
- Personality summary (1-2 sentences)
- A memorable quirk
- Voice/speech pattern suggestion

Keep it concise and immediately usable. Focus on what makes this NPC memorable and distinct."""

DETAILED_NPC_PROMPT = """You are an expert D&D 5e NPC generator. Create deep, three-dimensional NPCs with rich backgrounds and motivations.

For DETAILED mode, provide everything from quick mode PLUS:
- Background story (2-3 paragraphs)
- Current motivation/goals
- A secret or hidden aspect
- Ability scores (Str, Dex, Con, Int, Wis, Cha)
- Key skills
- Notable equipment/possessions

Make NPCs feel real and complex with layers that can be revealed through roleplay."""


@router.post("/generate", response_model=NPCResponse)
async def generate_npc(request: NPCRequest):
    """
    Generate a D&D NPC using Claude AI

    Modes:
    - quick: Fast generation with essentials only
    - detailed: Deep character with full background and stats
    """
    try:
        # Build the prompt based on request
        system_prompt = QUICK_NPC_PROMPT if request.mode == 'quick' else DETAILED_NPC_PROMPT

        # Build user message with constraints
        constraints = []
        if request.race:
            constraints.append(f"Race: {request.race}")
        if request.role:
            constraints.append(f"Role: {request.role}")
        if request.level:
            constraints.append(f"Level: {request.level}")
        if request.personality_trait:
            constraints.append(f"Personality trait: {request.personality_trait}")

        user_message = f"Generate a {request.mode} mode NPC"
        if constraints:
            user_message += " with the following requirements:\n" + "\n".join(f"- {c}" for c in constraints)
        else:
            user_message += " with random characteristics"

        user_message += "\n\nReturn ONLY a valid JSON object with the following structure:\n"

        if request.mode == 'quick':
            user_message += """{
  "name": "NPC name",
  "race": "race",
  "role": "occupation/role",
  "age": "age description",
  "appearance": "physical description",
  "personality": "personality summary",
  "quirk": "memorable quirk",
  "voice": "speech pattern or voice description"
}"""
        else:
            user_message += """{
  "name": "NPC name",
  "race": "race",
  "role": "occupation/role",
  "age": "age description",
  "appearance": "physical description",
  "personality": "personality summary",
  "quirk": "memorable quirk",
  "voice": "speech pattern or voice description",
  "background": "background story",
  "motivation": "current goals and motivations",
  "secret": "hidden aspect or secret",
  "stats": {
    "str": 10,
    "dex": 10,
    "con": 10,
    "int": 10,
    "wis": 10,
    "cha": 10
  },
  "skills": ["skill1", "skill2", "skill3"],
  "equipment": ["item1", "item2", "item3"]
}"""

        # Call Claude API
        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=2048 if request.mode == 'quick' else 4096,
            system=system_prompt,
            messages=[
                {
                    "role": "user",
                    "content": user_message
                }
            ]
        )

        # Extract and parse JSON response
        response_text = message.content[0].text

        # Try to extract JSON from the response
        try:
            # Sometimes Claude wraps JSON in markdown code blocks
            if "```json" in response_text:
                json_start = response_text.find("```json") + 7
                json_end = response_text.find("```", json_start)
                response_text = response_text[json_start:json_end].strip()
            elif "```" in response_text:
                json_start = response_text.find("```") + 3
                json_end = response_text.find("```", json_start)
                response_text = response_text[json_start:json_end].strip()

            npc_data = json.loads(response_text)
        except json.JSONDecodeError as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to parse NPC data: {str(e)}\nResponse: {response_text}"
            )

        # Add metadata
        npc_data['mode'] = request.mode
        npc_data['tokens_used'] = message.usage.input_tokens + message.usage.output_tokens

        # Return formatted response
        return NPCResponse(**npc_data)

    except json.JSONDecodeError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error parsing NPC data: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error generating NPC: {str(e)}"
        )


@router.get("/test")
async def test_npc():
    """
    Quick test endpoint to verify NPC generation is working
    """
    try:
        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=500,
            messages=[
                {
                    "role": "user",
                    "content": "Generate a quick NPC name and one-sentence description for a D&D tavern keeper."
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
            detail=f"NPC generation test failed: {str(e)}"
        )
