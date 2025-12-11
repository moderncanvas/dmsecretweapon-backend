"""
D&D DM Command Center - FastAPI Backend
Main application entry point
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# Create FastAPI app
app = FastAPI(
    title="D&D DM Command Center",
    description="AI-powered assistant for Dungeon Masters",
    version="0.1.0"
)

# Add Private Network Access support for Chrome (must be before CORS)
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

class PrivateNetworkAccessMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["Access-Control-Allow-Private-Network"] = "true"
        return response

app.add_middleware(PrivateNetworkAccessMiddleware)

# Enable CORS (Cross-Origin Resource Sharing) for frontend
# This allows your Svelte frontend to talk to this backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Import API routes
from app.api import chat, srd, npc, scene, random, combat, owlbear

# Register API routes
app.include_router(chat.router, prefix="/api", tags=["chat"])
app.include_router(srd.router, prefix="/api/srd", tags=["srd"])
app.include_router(npc.router, prefix="/api/npc", tags=["npc"])
app.include_router(scene.router, prefix="/api/scene", tags=["scene"])
app.include_router(random.router, prefix="/api/random", tags=["random"])
app.include_router(combat.router, prefix="/api/combat", tags=["combat"])
app.include_router(owlbear.router, tags=["owlbear"])


# Root endpoint - health check
@app.get("/")
async def root():
    """
    Health check endpoint - confirms the API is running
    """
    return {
        "status": "online",
        "app": "D&D DM Command Center",
        "version": "0.1.0"
    }


# Startup event
@app.on_event("startup")
async def startup_event():
    """
    Runs when the application starts
    """
    print("🎲 D&D DM Command Center is starting up...")
    print(f"📍 Environment: {os.getenv('ENVIRONMENT', 'development')}")
    print(f"🔑 API Key configured: {'✅' if os.getenv('ANTHROPIC_API_KEY') else '❌'}")
