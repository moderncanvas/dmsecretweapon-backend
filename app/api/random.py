"""
Random Generator API endpoint - creates random D&D content using Claude
"""

from fastapi import APIRouter, HTTPException
from anthropic import Anthropic
import os

from app.models.random import RandomRequest, RandomResponse

# Create router for random generation endpoints
router = APIRouter()

# Initialize Anthropic client
client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

# Generator-specific prompts
GENERATOR_PROMPTS = {
    'name': """Generate creative D&D character names. Consider the context for race/culture-specific names.
Examples: For elves use flowing, melodic names. For dwarves use strong, stone-related names. For humans use varied cultural influences.""",

    'loot': """Generate interesting loot and treasure for D&D. Include variety: coins, gems, art objects, mundane items, and occasional magic items.
Make items flavorful with specific details (e.g., "a silver locket with a painted portrait inside" rather than just "silver locket").""",

    'encounter': """Generate interesting random encounters for D&D. Include both combat and non-combat possibilities.
For combat encounters, suggest appropriate creatures. For non-combat, suggest interesting NPCs or situations.""",

    'plot_hook': """Generate compelling plot hooks that DMs can use to start adventures or side quests.
Make them specific enough to be interesting but flexible enough to fit different campaigns.""",

    'tavern_name': """Generate creative and memorable tavern/inn names for D&D.
Use patterns like "The [Adjective] [Noun]" or "[Noun] and [Noun]". Make them evocative and fun.""",

    'quest': """Generate short quest ideas for D&D. Include the basic premise and potential complications.
Keep them concise but interesting, suitable for side quests or adventure hooks.""",

    'rumor': """Generate rumors that players might hear in taverns, markets, or from NPCs.
Some should be true, some partially true, and some completely false. Make them intriguing.""",

    'trap': """Generate creative trap ideas for dungeons. Include both the trap mechanism and potential clues players might notice.
Vary between deadly, disabling, and alarm traps. Include mechanical and magical varieties."""
}


@router.post("/generate", response_model=RandomResponse)
async def generate_random(request: RandomRequest):
    """
    Generate random D&D content using Claude AI

    Generator types:
    - name: Character names (specify race/culture in context)
    - loot: Treasure and items (specify CR/location in context)
    - encounter: Random encounters (specify CR/terrain in context)
    - plot_hook: Adventure hooks and quest starters
    - tavern_name: Creative tavern and inn names
    - quest: Short quest ideas
    - rumor: Rumors and gossip for players to hear
    - trap: Trap ideas for dungeons
    """
    try:
        # Get the appropriate system prompt
        system_prompt = GENERATOR_PROMPTS.get(
            request.generator_type,
            "Generate creative D&D content based on the request."
        )

        # Build user message
        user_message = f"Generate {request.count} {request.generator_type}"

        if request.context:
            user_message += f" ({request.context})"

        user_message += ".\n\nReturn ONLY the results as a simple numbered list, one per line. "
        user_message += "Be concise but flavorful. Each result should be 1-3 sentences maximum."
        user_message += "\n\nExample format:\n1. First result\n2. Second result\n3. Third result"

        # Call Claude API
        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1024,
            system=system_prompt,
            messages=[
                {
                    "role": "user",
                    "content": user_message
                }
            ]
        )

        # Parse response into list
        response_text = message.content[0].text.strip()

        # Split by lines and clean up
        lines = [line.strip() for line in response_text.split('\n') if line.strip()]

        # Remove numbering and clean up
        results = []
        for line in lines:
            # Remove common numbering patterns
            cleaned = line
            # Remove "1. " or "1) " style numbering
            if len(line) > 2 and line[0].isdigit():
                if line[1] == '.' or line[1] == ')':
                    cleaned = line[2:].strip()
                elif len(line) > 3 and line[1].isdigit() and (line[2] == '.' or line[2] == ')'):
                    cleaned = line[3:].strip()

            # Remove leading dashes or asterisks
            cleaned = cleaned.lstrip('-*').strip()

            if cleaned:
                results.append(cleaned)

        # Return formatted response
        return RandomResponse(
            generator_type=request.generator_type,
            context=request.context,
            results=results[:request.count],  # Ensure we don't return more than requested
            tokens_used=message.usage.input_tokens + message.usage.output_tokens
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error generating random content: {str(e)}"
        )


@router.get("/types")
async def get_generator_types():
    """
    Get list of available generator types with descriptions
    """
    return {
        "generators": [
            {
                "type": "name",
                "label": "Character Names",
                "description": "Generate character names by race/culture",
                "context_hint": "e.g., elf, dwarf, human, orc",
                "icon": "👤"
            },
            {
                "type": "loot",
                "label": "Loot & Treasure",
                "description": "Generate treasure and items",
                "context_hint": "e.g., CR 5, dragon hoard, poor merchant",
                "icon": "💎"
            },
            {
                "type": "encounter",
                "label": "Random Encounters",
                "description": "Generate combat and non-combat encounters",
                "context_hint": "e.g., CR 3 forest, city streets, dungeon",
                "icon": "⚔️"
            },
            {
                "type": "plot_hook",
                "label": "Plot Hooks",
                "description": "Generate adventure hooks",
                "context_hint": "e.g., urban, wilderness, mystery",
                "icon": "📜"
            },
            {
                "type": "tavern_name",
                "label": "Tavern Names",
                "description": "Generate tavern and inn names",
                "context_hint": "e.g., fancy, dive bar, dwarven",
                "icon": "🍺"
            },
            {
                "type": "quest",
                "label": "Quest Ideas",
                "description": "Generate side quest ideas",
                "context_hint": "e.g., level 1-3, urban, rescue mission",
                "icon": "🗺️"
            },
            {
                "type": "rumor",
                "label": "Rumors",
                "description": "Generate rumors and gossip",
                "context_hint": "e.g., about local politics, monster sightings",
                "icon": "💬"
            },
            {
                "type": "trap",
                "label": "Traps",
                "description": "Generate trap ideas",
                "context_hint": "e.g., deadly, alarm, mechanical",
                "icon": "🪤"
            }
        ]
    }
