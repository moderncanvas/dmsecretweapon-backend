#!/usr/bin/env python3
"""
Asset Indexing Script

Scans the assets directory and builds a searchable index of all D&D assets.
Run this after downloading new assets to update the index.

Usage:
    python scripts/index_assets.py
"""

import sys
from pathlib import Path

# Add parent directory to path so we can import app modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.asset_service import AssetService


def main():
    """Index all assets in the assets directory"""
    print("=" * 60)
    print("D&D Asset Indexer")
    print("=" * 60)
    print()

    asset_service = AssetService()

    print(f"📁 Assets directory: {asset_service.assets_dir}")
    print()

    # Check if assets directory exists
    if not asset_service.assets_dir.exists():
        print("❌ Assets directory does not exist!")
        print(f"   Please create: {asset_service.assets_dir}")
        print()
        print("   Expected structure:")
        print("   data/assets/")
        print("   ├── forgotten_adventures/")
        print("   │   ├── tokens/")
        print("   │   └── maps/")
        print("   └── caeora/")
        print("       ├── tokens/")
        print("       └── maps/")
        return

    # Index assets
    print("🔍 Scanning for assets...")
    asset_service.index_assets()
    print()

    # Display results
    asset_count = len(asset_service.asset_index.get("assets", []))
    categories = asset_service.asset_index.get("categories", {})

    print("=" * 60)
    print("✅ Indexing complete!")
    print("=" * 60)
    print(f"Total assets indexed: {asset_count}")
    print()

    print("Categories:")
    for category, items in categories.items():
        print(f"  {category}: {len(items)} unique tags")

    print()
    print(f"Index saved to: {asset_service.index_file}")
    print()


if __name__ == "__main__":
    main()
