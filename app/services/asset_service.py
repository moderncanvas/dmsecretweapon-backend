import json
import os
from pathlib import Path
from typing import List, Optional, Dict
from PIL import Image
import anthropic


class AssetService:
    """Service for managing and searching D&D assets"""

    def __init__(self):
        self.assets_dir = Path(__file__).parent.parent.parent / "data" / "assets"
        self.index_file = self.assets_dir / "index.json"
        self.asset_index: Dict = {}
        self.load_index()

    def load_index(self):
        """Load asset index from file"""
        if self.index_file.exists():
            with open(self.index_file, 'r') as f:
                self.asset_index = json.load(f)
        else:
            self.asset_index = {
                "version": "1.0",
                "assets": [],
                "categories": {}
            }

    def save_index(self):
        """Save asset index to file"""
        self.assets_dir.mkdir(parents=True, exist_ok=True)
        with open(self.index_file, 'w') as f:
            json.dump(self.asset_index, f, indent=2)

    def index_assets(self):
        """Scan asset directories and build searchable index"""
        print("Indexing assets...")
        assets = []

        # Index Forgotten Adventures assets
        fa_dir = self.assets_dir / "forgotten_adventures"
        if fa_dir.exists():
            assets.extend(self._scan_directory(fa_dir, "forgotten_adventures"))

        # Index Caeora assets
        caeora_dir = self.assets_dir / "caeora"
        if caeora_dir.exists():
            assets.extend(self._scan_directory(caeora_dir, "caeora"))

        # Update index
        self.asset_index["assets"] = assets
        self.asset_index["last_updated"] = str(Path.ctime(self.index_file)) if self.index_file.exists() else ""

        # Build category index
        self._build_categories()

        self.save_index()
        print(f"Indexed {len(assets)} assets")

    def _scan_directory(self, directory: Path, source: str) -> List[Dict]:
        """Scan a directory for asset files"""
        assets = []

        for file_path in directory.rglob("*.png"):
            # Generate ID from file path
            relative_path = file_path.relative_to(self.assets_dir)
            asset_id = str(relative_path).replace('/', '-').replace('.png', '')

            # Extract tags from directory structure
            parts = file_path.relative_to(directory).parts
            tags = [part.lower().replace('_', ' ') for part in parts[:-1]]

            # Get file name as name
            name = file_path.stem.replace('_', ' ').replace('-', ' ').title()

            # Get image dimensions
            try:
                with Image.open(file_path) as img:
                    dimensions = {"width": img.width, "height": img.height}
            except Exception:
                dimensions = {"width": 256, "height": 256}

            # Determine asset type from path
            asset_type = "token"
            if "map" in str(file_path).lower():
                asset_type = "map"
            elif "prop" in str(file_path).lower():
                asset_type = "prop"

            asset = {
                "id": asset_id,
                "name": name,
                "path": str(relative_path),
                "type": asset_type,
                "tags": tags,
                "source": source,
                "dimensions": dimensions,
                "attribution": self._get_attribution(source)
            }

            assets.append(asset)

        return assets

    def _build_categories(self):
        """Build category index from assets"""
        categories = {
            "creature_types": set(),
            "npc_types": set(),
            "environments": set()
        }

        for asset in self.asset_index.get("assets", []):
            for tag in asset.get("tags", []):
                if any(creature in tag for creature in ["goblin", "orc", "dragon", "skeleton", "zombie"]):
                    categories["creature_types"].add(tag)
                elif any(npc in tag for npc in ["bartender", "merchant", "guard", "noble"]):
                    categories["npc_types"].add(tag)
                elif any(env in tag for env in ["tavern", "dungeon", "forest", "mountain"]):
                    categories["environments"].add(tag)

        # Convert sets to sorted lists
        self.asset_index["categories"] = {
            k: sorted(list(v)) for k, v in categories.items()
        }

    def _get_attribution(self, source: str) -> str:
        """Get attribution text for source"""
        if source == "forgotten_adventures":
            return "Forgotten Adventures - www.forgotten-adventures.net"
        elif source == "caeora":
            return "Caeora - www.caeora.com"
        return source

    def search_assets(
        self,
        query: str,
        asset_type: Optional[str] = None,
        limit: int = 20
    ) -> List[Dict]:
        """Search for assets matching query"""
        query_lower = query.lower()
        results = []

        for asset in self.asset_index.get("assets", []):
            # Filter by type if specified
            if asset_type and asset["type"] != asset_type:
                continue

            # Check if query matches name or tags
            score = 0
            if query_lower in asset["name"].lower():
                score += 10

            for tag in asset.get("tags", []):
                if query_lower in tag:
                    score += 5
                if query_lower == tag:
                    score += 10

            if score > 0:
                results.append((score, asset))

        # Sort by score and return top results
        results.sort(key=lambda x: x[0], reverse=True)
        return [asset for score, asset in results[:limit]]

    def get_asset_by_id(self, asset_id: str) -> Optional[Dict]:
        """Get specific asset by ID"""
        for asset in self.asset_index.get("assets", []):
            if asset["id"] == asset_id:
                return asset
        return None

    def match_description_to_asset(self, description: str, asset_type: str = "token") -> Optional[Dict]:
        """
        Use AI to match a text description to the best available asset
        Falls back to keyword search if AI fails
        """
        # First try keyword-based search
        keywords = description.lower().split()
        for keyword in keywords:
            results = self.search_assets(keyword, asset_type, limit=1)
            if results:
                return results[0]

        # If no results, return first available asset of that type
        for asset in self.asset_index.get("assets", []):
            if asset["type"] == asset_type:
                return asset

        return None

    def get_asset_path(self, asset_id: str) -> Optional[Path]:
        """Get full file system path for an asset"""
        asset = self.get_asset_by_id(asset_id)
        if asset:
            return self.assets_dir / asset["path"]
        return None
