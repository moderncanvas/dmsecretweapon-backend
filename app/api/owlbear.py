from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional
from pathlib import Path
from app.services.owlbear_service import OwlbearService
from app.services.asset_fetcher import AssetFetcher

router = APIRouter(prefix="/api/owlbear", tags=["owlbear"])

# Initialize services
owlbear_service = OwlbearService()
asset_fetcher = AssetFetcher()


# Request Models
class SceneGenerationRequest(BaseModel):
    description: str
    difficulty: Optional[str] = "medium"
    party_size: Optional[int] = 4


class TokenGenerationRequest(BaseModel):
    creature_type: str
    count: int = 1
    variant: Optional[str] = None


# API Endpoints
@router.post("/generate-scene")
async def generate_scene(request: SceneGenerationRequest):
    """
    Generate a complete scene with tokens based on description
    Assets are fetched dynamically from online sources

    Example:
    ```json
    {
      "description": "A dimly lit tavern with 3 patrons and a bartender",
      "difficulty": "easy",
      "party_size": 4
    }
    ```
    """
    try:
        scene_data = await owlbear_service.generate_scene(
            description=request.description,
            difficulty=request.difficulty,
            party_size=request.party_size
        )
        return scene_data
    except Exception as e:
        print(f"Scene generation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/generate-tokens")
async def generate_tokens(request: TokenGenerationRequest):
    """
    Generate tokens for specific creatures
    Assets are fetched dynamically from online sources

    Example:
    ```json
    {
      "creature_type": "goblin",
      "count": 5,
      "variant": "raider"
    }
    ```
    """
    try:
        tokens_data = await owlbear_service.generate_tokens(
            creature_type=request.creature_type,
            count=request.count,
            variant=request.variant
        )
        return tokens_data
    except Exception as e:
        print(f"Token generation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/assets/cached/{asset_id}")
async def get_cached_asset(asset_id: str):
    """
    Get a cached asset file by ID

    Returns the actual image file from cache with appropriate headers
    """
    try:
        asset_path = asset_fetcher.get_cached_asset_path(asset_id)

        if not asset_path or not asset_path.exists():
            raise HTTPException(status_code=404, detail="Cached asset not found")

        # Determine media type from file extension
        media_type = "image/png"
        if asset_path.suffix == ".svg":
            media_type = "image/svg+xml"
        elif asset_path.suffix == ".jpg" or asset_path.suffix == ".jpeg":
            media_type = "image/jpeg"

        return FileResponse(
            asset_path,
            media_type=media_type,
            headers={
                "Cache-Control": "public, max-age=86400",  # Cache for 24 hours
                "Access-Control-Allow-Origin": "*"  # Allow CORS for Owlbear Rodeo
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error serving cached asset: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/cache/clear")
async def clear_cache(older_than_days: int = Query(7, ge=1, le=90)):
    """
    Clear cached assets older than specified days

    Default: 7 days
    """
    try:
        asset_fetcher.clear_cache(older_than_days)
        return {
            "message": f"Cache cleared successfully (files older than {older_than_days} days)",
            "cache_dir": str(asset_fetcher.cache_dir)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/cache/info")
async def get_cache_info():
    """
    Get information about the asset cache

    Returns cache size, file count, and directory location
    """
    try:
        cache_files = list(asset_fetcher.cache_dir.glob("*"))
        total_size = sum(f.stat().st_size for f in cache_files if f.is_file())

        return {
            "cache_dir": str(asset_fetcher.cache_dir),
            "file_count": len(cache_files),
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "files": [
                {
                    "name": f.name,
                    "size_kb": round(f.stat().st_size / 1024, 2)
                }
                for f in cache_files[:20]  # Show first 20 files
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/placeholder.svg")
async def get_placeholder_svg():
    """
    Serve a simple placeholder token SVG
    """
    from starlette.responses import Response

    svg_content = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
  <circle cx="50" cy="50" r="45" fill="#4a5568" stroke="#718096" stroke-width="2"/>
  <text x="50" y="58" font-family="Arial" font-size="16" fill="white" text-anchor="middle">?</text>
</svg>"""

    return Response(
        content=svg_content,
        media_type="image/svg+xml",
        headers={
            "Cache-Control": "public, max-age=86400",
            "Access-Control-Allow-Origin": "*"
        }
    )


@router.get("/health")
async def health_check():
    """
    Health check endpoint for Owlbear integration

    Verifies that all services are working
    """
    import os

    return {
        "status": "healthy",
        "services": {
            "owlbear_service": "ok",
            "asset_fetcher": "ok",
            "anthropic_api": "configured" if os.getenv("ANTHROPIC_API_KEY") else "missing"
        },
        "cache_dir": str(asset_fetcher.cache_dir),
        "cache_exists": asset_fetcher.cache_dir.exists()
    }
