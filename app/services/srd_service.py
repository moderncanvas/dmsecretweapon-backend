"""
5e SRD Data Service
Loads D&D 5e SRD data into ChromaDB for semantic search
"""

import json
import os
from pathlib import Path
from typing import List, Dict, Any
import chromadb
from chromadb.config import Settings

# Path to SRD data
SRD_PATH = Path(__file__).parent.parent.parent / "data" / "srd-source" / "src" / "2014"
CHROMA_PATH = Path(__file__).parent.parent.parent / "data" / "chroma"

class SRDService:
    """Service for managing D&D 5e SRD data in ChromaDB"""

    def __init__(self):
        """Initialize ChromaDB client and collections"""
        # Create ChromaDB client (persistent storage)
        self.client = chromadb.PersistentClient(
            path=str(CHROMA_PATH),
            settings=Settings(anonymized_telemetry=False)
        )

        # Create or get collections for different data types
        self.collections = {
            'spells': self.client.get_or_create_collection("spells"),
            'monsters': self.client.get_or_create_collection("monsters"),
            'conditions': self.client.get_or_create_collection("conditions"),
            'magic_items': self.client.get_or_create_collection("magic_items"),
            'rules': self.client.get_or_create_collection("rules"),
        }

    def load_srd_data(self, force_reload: bool = False):
        """
        Load all SRD data into ChromaDB

        Args:
            force_reload: If True, delete existing data and reload
        """
        print("🎲 Loading D&D 5e SRD data into ChromaDB...")

        # Check if data already loaded
        if not force_reload:
            spells_count = self.collections['spells'].count()
            if spells_count > 0:
                print(f"✅ SRD data already loaded ({spells_count} spells found)")
                return

        # Load each data type
        self._load_spells()
        self._load_monsters()
        self._load_conditions()
        self._load_magic_items()
        self._load_rules()

        print("✅ SRD data loaded successfully!")

    def _load_spells(self):
        """Load spells into ChromaDB"""
        file_path = SRD_PATH / "5e-SRD-Spells.json"
        with open(file_path, 'r') as f:
            data = json.load(f)

        if not data:
            print("⚠️  No spells found")
            return

        # Prepare data for ChromaDB
        ids = []
        documents = []
        metadatas = []

        for spell in data:
            spell_id = f"spell_{spell['index']}"

            # Create searchable text combining all spell info
            doc_text = f"{spell['name']}\n"
            doc_text += f"Level {spell['level']} {spell.get('school', {}).get('name', '')}\n"
            doc_text += f"{spell.get('desc', [''])[0]}\n"
            doc_text += f"Range: {spell.get('range', '')}\n"
            doc_text += f"Duration: {spell.get('duration', '')}\n"

            ids.append(spell_id)
            documents.append(doc_text)
            metadatas.append({
                'name': spell['name'],
                'level': spell['level'],
                'school': spell.get('school', {}).get('name', ''),
                'type': 'spell'
            })

        # Add to ChromaDB
        self.collections['spells'].add(
            ids=ids,
            documents=documents,
            metadatas=metadatas
        )

        print(f"📜 Loaded {len(ids)} spells")

    def _load_monsters(self):
        """Load monsters into ChromaDB"""
        file_path = SRD_PATH / "5e-SRD-Monsters.json"
        with open(file_path, 'r') as f:
            data = json.load(f)

        if not data:
            print("⚠️  No monsters found")
            return

        ids = []
        documents = []
        metadatas = []

        for monster in data:
            monster_id = f"monster_{monster['index']}"

            # Create searchable text
            doc_text = f"{monster['name']}\n"
            doc_text += f"{monster.get('size', '')} {monster.get('type', '')}\n"
            doc_text += f"CR {monster.get('challenge_rating', 0)}\n"
            doc_text += f"AC {monster.get('armor_class', [{}])[0].get('value', 0)}, "
            doc_text += f"HP {monster.get('hit_points', 0)}\n"

            # Add special abilities
            if monster.get('special_abilities'):
                doc_text += "Special Abilities: " + ", ".join([
                    ability['name'] for ability in monster['special_abilities']
                ]) + "\n"

            ids.append(monster_id)
            documents.append(doc_text)
            metadatas.append({
                'name': monster['name'],
                'cr': float(monster.get('challenge_rating', 0)),
                'type': 'monster',
                'size': monster.get('size', '')
            })

        self.collections['monsters'].add(
            ids=ids,
            documents=documents,
            metadatas=metadatas
        )

        print(f"👹 Loaded {len(ids)} monsters")

    def _load_conditions(self):
        """Load conditions into ChromaDB"""
        file_path = SRD_PATH / "5e-SRD-Conditions.json"
        with open(file_path, 'r') as f:
            data = json.load(f)

        if not data:
            print("⚠️  No conditions found")
            return

        ids = []
        documents = []
        metadatas = []

        for condition in data:
            condition_id = f"condition_{condition['index']}"

            doc_text = f"{condition['name']}\n"
            doc_text += "\n".join(condition.get('desc', []))

            ids.append(condition_id)
            documents.append(doc_text)
            metadatas.append({
                'name': condition['name'],
                'type': 'condition'
            })

        self.collections['conditions'].add(
            ids=ids,
            documents=documents,
            metadatas=metadatas
        )

        print(f"🎭 Loaded {len(ids)} conditions")

    def _load_magic_items(self):
        """Load magic items into ChromaDB"""
        file_path = SRD_PATH / "5e-SRD-Magic-Items.json"
        with open(file_path, 'r') as f:
            data = json.load(f)

        if not data:
            print("⚠️  No magic items found")
            return

        ids = []
        documents = []
        metadatas = []

        for item in data:
            item_id = f"item_{item['index']}"

            doc_text = f"{item['name']}\n"
            doc_text += f"{item.get('equipment_category', {}).get('name', '')}\n"
            doc_text += "\n".join(item.get('desc', []))

            ids.append(item_id)
            documents.append(doc_text)
            metadatas.append({
                'name': item['name'],
                'rarity': item.get('rarity', {}).get('name', ''),
                'type': 'magic_item'
            })

        self.collections['magic_items'].add(
            ids=ids,
            documents=documents,
            metadatas=metadatas
        )

        print(f"✨ Loaded {len(ids)} magic items")

    def _load_rules(self):
        """Load rules into ChromaDB"""
        file_path = SRD_PATH / "5e-SRD-Rules.json"
        with open(file_path, 'r') as f:
            data = json.load(f)

        if not data:
            print("⚠️  No rules found")
            return

        ids = []
        documents = []
        metadatas = []

        for rule in data:
            rule_id = f"rule_{rule['index']}"

            doc_text = f"{rule['name']}\n"
            doc_text += f"{rule.get('desc', '')}"

            ids.append(rule_id)
            documents.append(doc_text)
            metadatas.append({
                'name': rule['name'],
                'type': 'rule'
            })

        self.collections['rules'].add(
            ids=ids,
            documents=documents,
            metadatas=metadatas
        )

        print(f"📖 Loaded {len(ids)} rules")

    def search(self, query: str, collection_name: str = 'all', n_results: int = 5) -> List[Dict[str, Any]]:
        """
        Search SRD data

        Args:
            query: Search query
            collection_name: Which collection to search ('all', 'spells', 'monsters', etc.)
            n_results: Number of results to return

        Returns:
            List of matching results
        """
        results = []

        # Determine which collections to search
        if collection_name == 'all':
            collections_to_search = self.collections.values()
        elif collection_name in self.collections:
            collections_to_search = [self.collections[collection_name]]
        else:
            return []

        # Search each collection
        for collection in collections_to_search:
            try:
                search_results = collection.query(
                    query_texts=[query],
                    n_results=n_results
                )

                # Format results
                for i in range(len(search_results['ids'][0])):
                    results.append({
                        'id': search_results['ids'][0][i],
                        'text': search_results['documents'][0][i],
                        'metadata': search_results['metadatas'][0][i],
                        'distance': search_results['distances'][0][i] if 'distances' in search_results else None
                    })
            except Exception as e:
                print(f"Error searching collection: {e}")
                continue

        # Sort by distance (lower is better)
        results.sort(key=lambda x: x['distance'] if x['distance'] is not None else float('inf'))

        return results[:n_results]


# Global instance
_srd_service = None

def get_srd_service() -> SRDService:
    """Get or create global SRD service instance"""
    global _srd_service
    if _srd_service is None:
        _srd_service = SRDService()
    return _srd_service
