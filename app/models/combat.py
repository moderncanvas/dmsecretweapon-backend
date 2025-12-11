"""
Combat Tracker Models
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class Combatant(BaseModel):
    """Model for a single combatant in initiative"""
    id: str
    name: str
    initiative: int
    hp_current: int
    hp_max: int
    ac: Optional[int] = None
    type: str = Field(..., description="'player', 'npc', or 'monster'")
    conditions: List[str] = []
    notes: str = ""
    monster_index: Optional[str] = None  # For linking to SRD monster data


class CombatState(BaseModel):
    """Model for the entire combat state"""
    id: str
    name: str = "Combat Encounter"
    combatants: List[Combatant]
    current_turn: int = 0
    round_number: int = 1
    is_active: bool = True
    created_at: str
    updated_at: str


class AddCombatantRequest(BaseModel):
    """Request to add a combatant"""
    combat_id: str
    name: str
    initiative: int
    hp_current: int
    hp_max: int
    ac: Optional[int] = None
    type: str = "npc"
    monster_index: Optional[str] = None


class UpdateHPRequest(BaseModel):
    """Request to update HP"""
    combat_id: str
    combatant_id: str
    hp_change: int  # Positive for healing, negative for damage


class AddConditionRequest(BaseModel):
    """Request to add a condition"""
    combat_id: str
    combatant_id: str
    condition: str


class RemoveConditionRequest(BaseModel):
    """Request to remove a condition"""
    combat_id: str
    combatant_id: str
    condition: str


class NextTurnRequest(BaseModel):
    """Request to advance to next turn"""
    combat_id: str


class CreateCombatRequest(BaseModel):
    """Request to create a new combat"""
    name: str = "Combat Encounter"
