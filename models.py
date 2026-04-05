"""Pydantic models for the Rasoi (Indian Cooking) environment."""

from enum import Enum
from typing import Any, Dict, List, Optional

from openenv.core.env_server.types import Action, Observation, State
from pydantic import Field, model_validator


class ActionType(str, Enum):
    ADD_INGREDIENT = "add_ingredient"
    SET_HEAT = "set_heat"
    COOK = "cook"
    STIR = "stir"
    CHOP = "chop"
    MIX = "mix"
    TRANSFER = "transfer"
    SERVE = "serve"
    CHECK_STATUS = "check_status"
    WAIT = "wait"


class HeatLevel(str, Enum):
    OFF = "off"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class ChopStyle(str, Enum):
    DICE = "dice"
    MINCE = "mince"
    SLICE = "slice"
    JULIENNE = "julienne"


class RasoiAction(Action):
    """Action the agent can take in the kitchen."""

    action_type: ActionType = Field(..., description="Type of cooking action")
    ingredient: Optional[str] = Field(None, description="Ingredient name (for add_ingredient, chop)")
    quantity: Optional[str] = Field(None, description="Quantity string e.g. '2 cups', '1 tsp'")
    vessel: Optional[str] = Field(None, description="Target vessel name")
    heat_level: Optional[HeatLevel] = Field(None, description="Heat level (for set_heat)")
    duration_minutes: Optional[int] = Field(None, ge=1, description="Duration in minutes (for cook, wait)")
    chop_style: Optional[ChopStyle] = Field(None, description="How to chop (for chop)")
    from_vessel: Optional[str] = Field(None, description="Source vessel (for transfer)")
    to_vessel: Optional[str] = Field(None, description="Destination vessel (for transfer)")
    dish_name: Optional[str] = Field(None, description="Name of dish being served (for serve)")

    @model_validator(mode="after")
    def validate_action_params(self) -> "RasoiAction":
        t = self.action_type
        if t == ActionType.ADD_INGREDIENT:
            if not self.ingredient:
                raise ValueError("add_ingredient requires 'ingredient'")
            if not self.vessel:
                raise ValueError("add_ingredient requires 'vessel'")
        elif t == ActionType.SET_HEAT:
            if not self.vessel:
                raise ValueError("set_heat requires 'vessel'")
            if self.heat_level is None:
                raise ValueError("set_heat requires 'heat_level'")
        elif t == ActionType.COOK:
            if not self.vessel:
                raise ValueError("cook requires 'vessel'")
            if self.duration_minutes is None:
                raise ValueError("cook requires 'duration_minutes'")
        elif t == ActionType.STIR:
            if not self.vessel:
                raise ValueError("stir requires 'vessel'")
        elif t == ActionType.CHOP:
            if not self.ingredient:
                raise ValueError("chop requires 'ingredient'")
            if self.chop_style is None:
                raise ValueError("chop requires 'chop_style'")
        elif t == ActionType.MIX:
            if not self.vessel:
                raise ValueError("mix requires 'vessel'")
        elif t == ActionType.TRANSFER:
            if not self.from_vessel:
                raise ValueError("transfer requires 'from_vessel'")
            if not self.to_vessel:
                raise ValueError("transfer requires 'to_vessel'")
        elif t == ActionType.SERVE:
            if not self.vessel:
                raise ValueError("serve requires 'vessel'")
        elif t == ActionType.CHECK_STATUS:
            if not self.vessel:
                raise ValueError("check_status requires 'vessel'")
        elif t == ActionType.WAIT:
            if self.duration_minutes is None:
                raise ValueError("wait requires 'duration_minutes'")
        return self


class RasoiObservation(Observation):
    """What the agent observes after each action."""

    vessels: Dict[str, Dict[str, Any]] = Field(
        default_factory=dict, description="State of each vessel"
    )
    available_ingredients: List[str] = Field(
        default_factory=list, description="Pantry items with quantities"
    )
    recipe: str = Field(default="", description="Recipe instructions")
    current_time: float = Field(default=0.0, description="Elapsed minutes")
    dietary_constraints: List[str] = Field(
        default_factory=list, description="Active dietary restrictions"
    )
    feedback: str = Field(default="", description="Result of last action")
    completed_dishes: List[str] = Field(
        default_factory=list, description="Dishes served so far"
    )
    score: float = Field(default=0.0, description="Current accumulated score")
    task_id: str = Field(default="task_1", description="Current task identifier")


class RasoiState(State):
    """Full internal state of the cooking environment."""

    task_id: str = Field(default="task_1")
    current_time: float = Field(default=0.0)
    completed_dishes: List[str] = Field(default_factory=list)
    score: float = Field(default=0.0)
    cumulative_reward: float = Field(default=0.0)
    vessels_summary: Dict[str, Any] = Field(default_factory=dict)
