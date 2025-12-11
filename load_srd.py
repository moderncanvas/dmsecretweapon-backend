#!/usr/bin/env python3
"""
Script to load 5e SRD data into ChromaDB
Run this once to initialize the database
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from app.services.srd_service import get_srd_service

if __name__ == "__main__":
    print("🎲 D&D 5e SRD Data Loader")
    print("=" * 50)

    srd = get_srd_service()
    srd.load_srd_data(force_reload=False)

    print("\n✅ Done! SRD data is ready for searching.")
    print("\nYou can now:")
    print("  - Search spells, monsters, conditions, magic items, and rules")
    print("  - Use semantic search (e.g., 'fire damage spells')")
    print("  - Ask Claude about specific D&D content")
