import os
import httpx
import hashlib
from pathlib import Path
from typing import Optional, Dict, List
from bs4 import BeautifulSoup
import anthropic


class AssetFetcher:
    """Service for dynamically fetching D&D assets from online sources"""

    def __init__(self):
        self.cache_dir = Path(__file__).parent.parent.parent / "data" / "asset_cache"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

        # Asset source URLs
        self.sources = {
            "forgotten_adventures": {
                "base_url": "https://www.forgotten-adventures.net",
                "tokens_url": "https://www.forgotten-adventures.net/tokens-library/",
            },
            "caeora": {
                "base_url": "https://www.caeora.com",
                "tokens_url": "https://www.caeora.com/map-gallery",
            },
            "game_icons": {
                "base_url": "https://game-icons.net",
                "api_url": "https://game-icons.net/api/",
            }
        }

    async def fetch_token_for_description(self, description: str, token_type: str = "creature") -> Optional[Dict]:
        """
        Fetch a token asset that matches the description

        Args:
            description: Description of what token is needed (e.g., "goblin warrior", "bartender")
            token_type: Type of token (creature, npc, player, prop)

        Returns:
            Dict with asset info including URL, or None if not found
        """
        # Try different sources in order of preference
        sources_priority = ["game_icons", "forgotten_adventures", "caeora"]

        for source in sources_priority:
            asset = await self._fetch_from_source(description, source, token_type)
            if asset:
                return asset

        # Fallback to placeholder
        return await self._get_placeholder_token(description)

    async def _fetch_from_source(self, description: str, source: str, token_type: str) -> Optional[Dict]:
        """Fetch asset from a specific source"""
        if source == "game_icons":
            return await self._fetch_from_game_icons(description)
        elif source == "forgotten_adventures":
            return await self._fetch_from_forgotten_adventures(description, token_type)
        elif source == "caeora":
            return await self._fetch_from_caeora(description, token_type)
        return None

    async def _fetch_from_game_icons(self, description: str) -> Optional[Dict]:
        """
        Fetch token from game-icons.net
        This is a free, open source icon library with an API
        """
        try:
            # Use AI to extract search keywords from description
            keywords = await self._extract_keywords(description)

            async with httpx.AsyncClient(timeout=30.0) as client:
                # Search for icon
                for keyword in keywords[:3]:  # Try top 3 keywords
                    search_url = f"https://game-icons.net/tags/{keyword.replace(' ', '-')}.html"

                    try:
                        response = await client.get(search_url)
                        if response.status_code == 200:
                            # Parse HTML to find icon
                            soup = BeautifulSoup(response.text, 'html.parser')
                            icon_divs = soup.find_all('div', class_='icon')

                            if icon_divs:
                                # Get first matching icon
                                first_icon = icon_divs[0]
                                icon_link = first_icon.find('a')
                                if icon_link:
                                    icon_name = icon_link['href'].split('/')[-1].replace('.html', '')

                                    # Generate SVG URL
                                    svg_url = f"https://game-icons.net/icons/ffffff/000000/1x1/{icon_name}.svg"

                                    # Download and cache
                                    cached_path = await self._cache_asset(svg_url, f"game-icons-{icon_name}")

                                    return {
                                        "id": f"game-icons-{icon_name}",
                                        "name": icon_name.replace('-', ' ').title(),
                                        "url": svg_url,
                                        "cached_path": str(cached_path),
                                        "source": "game-icons.net",
                                        "attribution": "Game-icons.net - CC BY 3.0",
                                        "type": "token"
                                    }
                    except Exception:
                        continue

        except Exception as e:
            print(f"Error fetching from game-icons: {e}")

        return None

    async def _fetch_from_forgotten_adventures(self, description: str, token_type: str) -> Optional[Dict]:
        """
        Fetch from Forgotten Adventures
        Note: This would require their API or web scraping with permission
        For now, returns None and focuses on game-icons
        """
        # FA doesn't have a public API, so we'd need to implement web scraping
        # or use their Patreon API if available
        # For now, we'll skip this and use game-icons as primary source
        return None

    async def _fetch_from_caeora(self, description: str, token_type: str) -> Optional[Dict]:
        """
        Fetch from Caeora
        Note: Similar to FA, would need API or scraping
        """
        return None

    async def _extract_keywords(self, description: str) -> List[str]:
        """Use AI to extract search keywords from description"""
        try:
            prompt = f"""Extract 3 relevant search keywords from this description for finding fantasy RPG icons/tokens.
Description: {description}

Return only the keywords, one per line, most relevant first.
Examples:
- "goblin warrior with a sword" -> goblin, warrior, sword
- "elderly bartender" -> bartender, old, human
- "red dragon" -> dragon, red, monster"""

            response = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=100,
                messages=[{"role": "user", "content": prompt}]
            )

            keywords = response.content[0].text.strip().split('\n')
            # Clean up keywords
            keywords = [k.strip('- ').strip().lower() for k in keywords if k.strip()]
            return keywords[:3]

        except Exception as e:
            print(f"Error extracting keywords: {e}")
            # Fallback to simple word extraction
            return description.lower().split()[:3]

    async def _cache_asset(self, url: str, asset_id: str) -> Path:
        """Download and cache an asset file"""
        # Generate cache filename
        url_hash = hashlib.md5(url.encode()).hexdigest()[:8]
        file_ext = Path(url).suffix or '.png'
        cache_file = self.cache_dir / f"{asset_id}-{url_hash}{file_ext}"

        # Return if already cached
        if cache_file.exists():
            return cache_file

        # Download asset
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(url)
                response.raise_for_status()

                # Save to cache
                with open(cache_file, 'wb') as f:
                    f.write(response.content)

                return cache_file

        except Exception as e:
            print(f"Error caching asset: {e}")
            raise

    async def _get_placeholder_token(self, description: str) -> Dict:
        """Generate a placeholder token when no asset is found"""
        # Create a simple colored circle as placeholder
        placeholder_id = f"placeholder-{hashlib.md5(description.encode()).hexdigest()[:8]}"

        # Use our own placeholder endpoint - always reliable
        # Note: This will be converted to full URL in owlbear_service
        fallback_url = "/api/owlbear/placeholder.svg"

        return {
            "id": placeholder_id,
            "name": description.title(),
            "url": fallback_url,
            "cached_path": None,  # Don't cache placeholder
            "source": "placeholder",
            "attribution": "Generated placeholder",
            "type": "token"
        }

    def get_cached_asset_path(self, asset_id: str) -> Optional[Path]:
        """Get path to cached asset by ID"""
        # Search cache directory for matching file
        for file in self.cache_dir.glob(f"{asset_id}-*"):
            return file
        return None

    def clear_cache(self, older_than_days: int = 7):
        """Clear cached assets older than specified days"""
        import time
        cutoff_time = time.time() - (older_than_days * 86400)

        for file in self.cache_dir.glob("*"):
            if file.stat().st_mtime < cutoff_time:
                file.unlink()

        print(f"Cleared cache files older than {older_than_days} days")
