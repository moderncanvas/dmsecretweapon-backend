"""
Combat Tracker API endpoint - manages initiative and combat state
"""

from fastapi import APIRouter, HTTPException
from typing import Dict
import uuid
from datetime import datetime

from app.models.combat import (
    CombatState,
    Combatant,
    CreateCombatRequest,
    AddCombatantRequest,
    UpdateHPRequest,
    AddConditionRequest,
    RemoveConditionRequest,
    NextTurnRequest
)

# Create router for combat endpoints
router = APIRouter()

# In-memory storage for combat sessions (could be moved to database later)
active_combats: Dict[str, CombatState] = {}


@router.post("/create", response_model=CombatState)
async def create_combat(request: CreateCombatRequest):
    """Create a new combat encounter"""
    combat_id = str(uuid.uuid4())
    now = datetime.utcnow().isoformat()

    combat = CombatState(
        id=combat_id,
        name=request.name,
        combatants=[],
        current_turn=0,
        round_number=1,
        is_active=True,
        created_at=now,
        updated_at=now
    )

    active_combats[combat_id] = combat
    return combat


@router.get("/{combat_id}", response_model=CombatState)
async def get_combat(combat_id: str):
    """Get combat state by ID"""
    if combat_id not in active_combats:
        raise HTTPException(status_code=404, detail="Combat not found")

    return active_combats[combat_id]


@router.get("/", response_model=list[CombatState])
async def list_combats():
    """List all active combats"""
    return list(active_combats.values())


@router.post("/add-combatant", response_model=CombatState)
async def add_combatant(request: AddCombatantRequest):
    """Add a combatant to the initiative order"""
    if request.combat_id not in active_combats:
        raise HTTPException(status_code=404, detail="Combat not found")

    combat = active_combats[request.combat_id]

    # Create new combatant
    combatant = Combatant(
        id=str(uuid.uuid4()),
        name=request.name,
        initiative=request.initiative,
        hp_current=request.hp_current,
        hp_max=request.hp_max,
        ac=request.ac,
        type=request.type,
        conditions=[],
        notes="",
        monster_index=request.monster_index
    )

    # Add to combat
    combat.combatants.append(combatant)

    # Sort by initiative (highest first)
    combat.combatants.sort(key=lambda c: c.initiative, reverse=True)

    combat.updated_at = datetime.utcnow().isoformat()
    return combat


@router.post("/update-hp", response_model=CombatState)
async def update_hp(request: UpdateHPRequest):
    """Update a combatant's HP (damage or healing)"""
    if request.combat_id not in active_combats:
        raise HTTPException(status_code=404, detail="Combat not found")

    combat = active_combats[request.combat_id]

    # Find combatant
    combatant = next((c for c in combat.combatants if c.id == request.combatant_id), None)
    if not combatant:
        raise HTTPException(status_code=404, detail="Combatant not found")

    # Update HP
    combatant.hp_current += request.hp_change
    combatant.hp_current = max(0, min(combatant.hp_current, combatant.hp_max))

    combat.updated_at = datetime.utcnow().isoformat()
    return combat


@router.post("/add-condition", response_model=CombatState)
async def add_condition(request: AddConditionRequest):
    """Add a condition to a combatant"""
    if request.combat_id not in active_combats:
        raise HTTPException(status_code=404, detail="Combat not found")

    combat = active_combats[request.combat_id]

    # Find combatant
    combatant = next((c for c in combat.combatants if c.id == request.combatant_id), None)
    if not combatant:
        raise HTTPException(status_code=404, detail="Combatant not found")

    # Add condition if not already present
    if request.condition not in combatant.conditions:
        combatant.conditions.append(request.condition)

    combat.updated_at = datetime.utcnow().isoformat()
    return combat


@router.post("/remove-condition", response_model=CombatState)
async def remove_condition(request: RemoveConditionRequest):
    """Remove a condition from a combatant"""
    if request.combat_id not in active_combats:
        raise HTTPException(status_code=404, detail="Combat not found")

    combat = active_combats[request.combat_id]

    # Find combatant
    combatant = next((c for c in combat.combatants if c.id == request.combatant_id), None)
    if not combatant:
        raise HTTPException(status_code=404, detail="Combatant not found")

    # Remove condition
    if request.condition in combatant.conditions:
        combatant.conditions.remove(request.condition)

    combat.updated_at = datetime.utcnow().isoformat()
    return combat


@router.post("/next-turn", response_model=CombatState)
async def next_turn(request: NextTurnRequest):
    """Advance to the next turn in initiative"""
    if request.combat_id not in active_combats:
        raise HTTPException(status_code=404, detail="Combat not found")

    combat = active_combats[request.combat_id]

    if not combat.combatants:
        raise HTTPException(status_code=400, detail="No combatants in initiative")

    # Advance turn
    combat.current_turn += 1

    # Check if we've completed a round
    if combat.current_turn >= len(combat.combatants):
        combat.current_turn = 0
        combat.round_number += 1

    combat.updated_at = datetime.utcnow().isoformat()
    return combat


@router.delete("/{combat_id}/combatant/{combatant_id}", response_model=CombatState)
async def remove_combatant(combat_id: str, combatant_id: str):
    """Remove a combatant from combat"""
    if combat_id not in active_combats:
        raise HTTPException(status_code=404, detail="Combat not found")

    combat = active_combats[combat_id]

    # Remove combatant
    combat.combatants = [c for c in combat.combatants if c.id != combatant_id]

    # Adjust current_turn if needed
    if combat.current_turn >= len(combat.combatants) and combat.combatants:
        combat.current_turn = 0

    combat.updated_at = datetime.utcnow().isoformat()
    return combat


@router.delete("/{combat_id}")
async def delete_combat(combat_id: str):
    """End and delete a combat encounter"""
    if combat_id not in active_combats:
        raise HTTPException(status_code=404, detail="Combat not found")

    del active_combats[combat_id]
    return {"message": "Combat deleted successfully"}


@router.get("/conditions/list")
async def list_conditions():
    """Get list of common D&D 5e conditions"""
    return {
        "conditions": [
            "Blinded",
            "Charmed",
            "Deafened",
            "Frightened",
            "Grappled",
            "Incapacitated",
            "Invisible",
            "Paralyzed",
            "Petrified",
            "Poisoned",
            "Prone",
            "Restrained",
            "Stunned",
            "Unconscious",
            "Exhaustion"
        ]
    }
