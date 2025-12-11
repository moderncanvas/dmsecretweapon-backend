import os
from typing import List, Dict, Optional
import anthropic
from app.services.asset_fetcher import AssetFetcher


class OwlbearService:
    """Service for generating Owlbear Rodeo scenes and tokens with dynamic asset fetching"""

    def __init__(self):
        self.client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        self.asset_fetcher = AssetFetcher()
        self.grid_size = 140  # OBR grid size in pixels
        # Get the base URL for asset serving (Railway deployment URL)
        self.base_url = os.getenv("RAILWAY_PUBLIC_DOMAIN", os.getenv("BASE_URL", "http://localhost:8000"))
        if not self.base_url.startswith("http"):
            self.base_url = f"https://{self.base_url}"

    async def generate_scene(
        self,
        description: str,
        difficulty: str = "medium",
        party_size: int = 4
    ) -> Dict:
        """Generate a complete scene with tokens, fetching assets on-demand"""

        # Generate scene using Claude
        prompt = f"""You are assisting a D&D DM by generating a scene for Owlbear Rodeo.

Scene Description: {description}
Party Size: {party_size}
Difficulty: {difficulty}

Generate a structured scene response with:
1. A scene name (short, evocative)
2. A read-aloud description (2-3 sentences, atmospheric)
3. A list of NPCs/creatures needed with:
   - name
   - type (npc, creature, or prop)
   - brief description for finding appropriate art/token
   - suggested role (friendly, neutral, hostile)
   - approximate HP and AC if it's a creature/npc

For difficulty:
- easy: 1-2 weak creatures or all friendly NPCs
- medium: 3-5 creatures mix of types
- hard: 6-8 creatures with some strong ones
- deadly: 9+ creatures or very powerful enemies

Return ONLY valid JSON in this exact format:
{{
  "scene_name": "The Rusty Flagon",
  "read_aloud": "The tavern smells of stale ale and smoke...",
  "tokens": [
    {{
      "name": "Gruff Bartender",
      "type": "npc",
      "description": "middle-aged human male bartender with apron",
      "role": "friendly",
      "hp": 15,
      "ac": 10
    }},
    {{
      "name": "Goblin Raider",
      "type": "creature",
      "description": "goblin with sword and leather armor",
      "role": "hostile",
      "hp": 7,
      "ac": 15
    }}
  ]
}}"""

        try:
            response = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=2000,
                messages=[{"role": "user", "content": prompt}]
            )

            # Parse JSON response
            import json
            content = response.content[0].text
            # Extract JSON from potential markdown code blocks
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()

            scene_data = json.loads(content)

        except Exception as e:
            print(f"Error generating scene with AI: {e}")
            # Fallback to simple scene
            scene_data = {
                "scene_name": "Generated Scene",
                "read_aloud": description,
                "tokens": [
                    {
                        "name": "Character",
                        "type": "npc",
                        "description": "generic character",
                        "role": "neutral",
                        "hp": 10,
                        "ac": 10
                    }
                ]
            }

        # Fetch assets for each token on-demand
        tokens_with_assets = []
        for i, token in enumerate(scene_data.get("tokens", [])):
            try:
                # Fetch asset dynamically
                asset = await self.asset_fetcher.fetch_token_for_description(
                    description=token.get("description", token.get("name", "")),
                    token_type=token.get("type", "npc")
                )

                if not asset:
                    print(f"No asset found for: {token.get('name')}")
                    continue

                # Generate position
                position = self._generate_position(i, len(scene_data.get("tokens", [])))

                # Construct asset URL - either from cache, relative path, or direct URL
                if asset.get("cached_path"):
                    asset_url = f"{self.base_url}/api/owlbear/assets/cached/{asset['id']}"
                elif asset["url"].startswith("/"):
                    # Relative URL - prepend base URL
                    asset_url = f"{self.base_url}{asset['url']}"
                else:
                    asset_url = asset["url"]

                tokens_with_assets.append({
                    "name": token.get("name"),
                    "type": token.get("type", "npc"),
                    "asset_url": asset_url,
                    "position": position,
                    "metadata": {
                        "hp": token.get("hp"),
                        "ac": token.get("ac"),
                        "role": token.get("role", "neutral"),
                        "attribution": asset.get("attribution", "")
                    }
                })

            except Exception as e:
                print(f"Error fetching asset for {token.get('name')}: {e}")
                continue

        return {
            "scene": {
                "name": scene_data.get("scene_name", "Generated Scene"),
                "description": description,
                "read_aloud": scene_data.get("read_aloud", description)
            },
            "tokens": tokens_with_assets
        }

    async def generate_tokens(
        self,
        creature_type: str,
        count: int = 1,
        variant: Optional[str] = None
    ) -> Dict:
        """Generate tokens for specific creatures, fetching assets on-demand"""

        tokens = []

        # Build description for asset search
        search_description = f"{creature_type} {variant}" if variant else creature_type

        for i in range(count):
            try:
                # Fetch asset dynamically
                asset = await self.asset_fetcher.fetch_token_for_description(
                    description=search_description,
                    token_type="creature"
                )

                if not asset:
                    print(f"No asset found for: {creature_type}")
                    continue

                # Generate stats based on creature type
                hp, ac = self._generate_stats(creature_type, variant)

                # Construct asset URL - either from cache, relative path, or direct URL
                if asset.get("cached_path"):
                    asset_url = f"{self.base_url}/api/owlbear/assets/cached/{asset['id']}"
                elif asset["url"].startswith("/"):
                    # Relative URL - prepend base URL
                    asset_url = f"{self.base_url}{asset['url']}"
                else:
                    asset_url = asset["url"]

                tokens.append({
                    "name": f"{creature_type} {i + 1}" if count > 1 else creature_type,
                    "type": "creature",
                    "asset_url": asset_url,
                    "metadata": {
                        "hp": hp,
                        "ac": ac,
                        "attribution": asset.get("attribution", "")
                    }
                })

            except Exception as e:
                print(f"Error generating token {i+1}: {e}")
                continue

        return {"tokens": tokens}

    def _generate_position(self, index: int, total: int) -> Dict[str, int]:
        """Generate smart position for token"""
        import math

        # Center of a 40x30 grid
        center_x = 20 * self.grid_size
        center_y = 15 * self.grid_size

        # Arrange in a circle
        angle = (index / total) * 2 * math.pi
        radius = self.grid_size * (3 + (total / 5))

        return {
            "x": int(center_x + math.cos(angle) * radius),
            "y": int(center_y + math.sin(angle) * radius)
        }

    def _generate_stats(self, creature_type: str, variant: Optional[str] = None) -> tuple[int, int]:
        """Generate HP and AC for creature type (simplified)"""
        creature_lower = creature_type.lower()

        # Simple lookup table
        stats = {
            "goblin": (7, 15),
            "orc": (15, 13),
            "skeleton": (13, 13),
            "zombie": (22, 8),
            "dragon": (200, 19),
            "wolf": (11, 13),
            "bear": (34, 11),
            "guard": (11, 16),
            "bandit": (11, 12),
            "kobold": (5, 12),
            "ogre": (59, 11),
            "troll": (84, 15),
        }

        # Check for known creature
        for key, (hp, ac) in stats.items():
            if key in creature_lower:
                # Adjust for variant
                if variant and "elite" in variant.lower():
                    return (hp * 2, ac + 2)
                return (hp, ac)

        # Default stats
        return (15, 12)
