"""
Scene Generator API endpoint - creates atmospheric D&D scenes using Claude
"""

from fastapi import APIRouter, HTTPException
from anthropic import Anthropic
import os
import json

from app.models.scene import SceneRequest, SceneResponse

# Create router for scene endpoints
router = APIRouter()

# Initialize Anthropic client
client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

# System prompt for scene generation
SCENE_GENERATOR_PROMPT = """You are an expert D&D storyteller specializing in creating immersive, atmospheric scene descriptions.

Your scenes should:
- Engage multiple senses (sight, sound, smell, touch, taste when appropriate)
- Create vivid mental images with specific, evocative details
- Match the requested mood and atmosphere
- Include both aesthetic and functional elements
- Provide read-aloud text that flows naturally
- Suggest practical DM notes for running the scene

Focus on "show don't tell" - use concrete sensory details rather than abstract descriptions."""


@router.post("/generate", response_model=SceneResponse)
async def generate_scene(request: SceneRequest):
    """
    Generate an atmospheric D&D scene description using Claude AI

    Scene types:
    - dungeon: Underground chambers, crypts, caves
    - tavern: Inns, bars, social gathering places
    - wilderness: Forests, mountains, plains
    - city: Urban streets, markets, buildings
    - temple: Churches, shrines, holy places
    - combat: Battle scenes, encounters
    - mystery: Puzzles, investigation scenes
    - social: Court intrigue, negotiations
    """
    try:
        # Build the prompt
        user_message = f"Generate a {request.scene_type} scene"

        if request.mood:
            user_message += f" with a {request.mood} mood"

        if request.setting_details:
            user_message += f". Setting details: {request.setting_details}"

        user_message += f"\n\nScene length: {request.length}"
        user_message += f"\nInclude sensory details: {request.include_sensory}"

        user_message += "\n\nReturn ONLY a valid JSON object with this structure:\n"
        user_message += """{
  "scene_type": "the scene type",
  "mood": "the dominant mood/atmosphere",
  "description": "brief summary of the scene",
  "read_aloud_text": "the atmospheric description to read to players (formatted for easy reading)",
  "dm_notes": "practical tips for running this scene, potential complications, or hidden details",
  "suggested_encounters": ["encounter idea 1", "encounter idea 2", "encounter idea 3"],
  "points_of_interest": ["interesting detail 1", "interesting detail 2", "interesting detail 3"]
}

For read_aloud_text:
- Write in present tense for immediacy
- Use vivid, specific sensory details
- Create atmosphere through description
- Include elements that invite player interaction
- Format with natural paragraph breaks for easy reading"""

        # Determine token limit based on length
        max_tokens = {
            'short': 1024,
            'medium': 2048,
            'long': 3072
        }.get(request.length, 2048)

        # Call Claude API
        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=max_tokens,
            system=SCENE_GENERATOR_PROMPT,
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

            scene_data = json.loads(response_text)
        except json.JSONDecodeError as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to parse scene data: {str(e)}\nResponse: {response_text}"
            )

        # Add metadata
        scene_data['tokens_used'] = message.usage.input_tokens + message.usage.output_tokens

        # Return formatted response
        return SceneResponse(**scene_data)

    except json.JSONDecodeError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error parsing scene data: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error generating scene: {str(e)}"
        )


@router.get("/test")
async def test_scene():
    """
    Quick test endpoint to verify scene generation is working
    """
    try:
        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=300,
            messages=[
                {
                    "role": "user",
                    "content": "Write a one-sentence atmospheric description of a mysterious tavern."
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
            detail=f"Scene generation test failed: {str(e)}"
        )
