"""
SRD Search API endpoints
Provides semantic search over D&D 5e SRD data
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

from app.services.srd_service import get_srd_service

router = APIRouter()

# Get SRD service
srd = get_srd_service()


class SearchRequest(BaseModel):
    """Search request model"""
    query: str = Field(..., description="Search query", min_length=1)
    collection: str = Field('all', description="Collection to search (all, spells, monsters, conditions, magic_items, rules)")
    limit: int = Field(5, description="Number of results", ge=1, le=20)


class SearchResult(BaseModel):
    """Single search result"""
    id: str
    name: str
    text: str
    type: str
    metadata: Dict[str, Any]
    relevance: Optional[float] = None


class SearchResponse(BaseModel):
    """Search response model"""
    query: str
    results: List[SearchResult]
    count: int


@router.post("/search", response_model=SearchResponse)
async def search_srd(request: SearchRequest):
    """
    Search D&D 5e SRD data

    **Examples:**
    - "fireball spell"
    - "CR 5 monsters"
    - "condition grappled"
    - "magic sword"
    """
    try:
        results = srd.search(
            query=request.query,
            collection_name=request.collection,
            n_results=request.limit
        )

        formatted_results = []
        for r in results:
            formatted_results.append(SearchResult(
                id=r['id'],
                name=r['metadata'].get('name', 'Unknown'),
                text=r['text'],
                type=r['metadata'].get('type', 'unknown'),
                metadata=r['metadata'],
                relevance=1 - r['distance'] if r['distance'] is not None else None
            ))

        return SearchResponse(
            query=request.query,
            results=formatted_results,
            count=len(formatted_results)
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Search error: {str(e)}"
        )


@router.get("/spells/{spell_name}")
async def get_spell(spell_name: str):
    """
    Get spell by name (fuzzy match)
    """
    results = srd.search(spell_name, collection_name='spells', n_results=1)

    if not results:
        raise HTTPException(status_code=404, detail=f"Spell '{spell_name}' not found")

    return {
        'name': results[0]['metadata'].get('name'),
        'details': results[0]['text'],
        'metadata': results[0]['metadata']
    }


@router.get("/monsters/{monster_name}")
async def get_monster(monster_name: str):
    """
    Get monster by name (fuzzy match)
    """
    results = srd.search(monster_name, collection_name='monsters', n_results=1)

    if not results:
        raise HTTPException(status_code=404, detail=f"Monster '{monster_name}' not found")

    return {
        'name': results[0]['metadata'].get('name'),
        'details': results[0]['text'],
        'metadata': results[0]['metadata']
    }


@router.get("/conditions/{condition_name}")
async def get_condition(condition_name: str):
    """
    Get condition by name (fuzzy match)
    """
    results = srd.search(condition_name, collection_name='conditions', n_results=1)

    if not results:
        raise HTTPException(status_code=404, detail=f"Condition '{condition_name}' not found")

    return {
        'name': results[0]['metadata'].get('name'),
        'details': results[0]['text'],
        'metadata': results[0]['metadata']
    }


@router.get("/stats")
async def get_stats():
    """
    Get SRD database statistics
    """
    return {
        'spells': srd.collections['spells'].count(),
        'monsters': srd.collections['monsters'].count(),
        'conditions': srd.collections['conditions'].count(),
        'magic_items': srd.collections['magic_items'].count(),
        'rules': srd.collections['rules'].count(),
    }
