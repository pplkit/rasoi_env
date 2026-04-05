"""Pydantic models for the Rasoi (Indian Cooking) environment."""

from typing import Any, Dict, List, Literal, Optional

from openenv.core.env_server.types import Action, Observation, State
from pydantic import Field, model_validator


ActionType = Literal[
    "add_ingredient", "set_heat", "cook", "stir", "chop",
    "mix", "transfer", "serve", "check_status", "wait",
]

HeatLevel = Literal["off", "low", "medium", "high"]

ChopStyle = Literal["dice", "mince", "slice", "julienne"]

Ingredient = Literal[
    "water", "ginger", "cinnamon_stick", "cardamom", "cloves",
    "tea_leaves", "milk", "oat_milk", "sugar", "salt",
    "flour", "baking_powder", "eggs", "butter", "coconut_oil",
    "moong_dal", "turmeric", "ghee", "cumin_seeds", "garlic",
    "green_chilies", "cilantro", "rice", "oil", "mustard_seeds",
    "onion", "potato", "cauliflower", "red_chili_powder",
]

Vessel = Literal[
    "saucepan", "cup", "mixing_bowl", "wet_bowl", "pan", "plate",
    "pot", "rice_pot", "small_pan", "wok", "cutting_board",
]

DishName = Literal["masala_chai", "pancakes", "dal", "jeera_rice", "aloo_gobi"]


class RasoiAction(Action):
    """Action the agent can take in the kitchen."""

    action_type: ActionType = Field(..., description="Type of cooking action")
    ingredient: Optional[Ingredient] = Field(None, description="Ingredient name (for add_ingredient, chop)")
    quantity: Optional[str] = Field(None, description="Quantity string e.g. '2 cups', '1 tsp'")
    vessel: Optional[Vessel] = Field(None, description="Target vessel name")
    heat_level: Optional[HeatLevel] = Field(None, description="Heat level (for set_heat)")
    duration_minutes: Optional[int] = Field(None, ge=1, description="Duration in minutes (for cook, wait)")
    chop_style: Optional[ChopStyle] = Field(None, description="How to chop (for chop)")
    from_vessel: Optional[Vessel] = Field(None, description="Source vessel (for transfer)")
    to_vessel: Optional[Vessel] = Field(None, description="Destination vessel (for transfer)")
    dish_name: Optional[DishName] = Field(None, description="Name of dish being served (for serve)")

    @model_validator(mode="after")
    def validate_action_params(self) -> "RasoiAction":
        t = self.action_type
        if t == "add_ingredient":
            if not self.ingredient:
                raise ValueError("add_ingredient requires 'ingredient'")
            if not self.vessel:
                raise ValueError("add_ingredient requires 'vessel'")
        elif t == "set_heat":
            if not self.vessel:
                raise ValueError("set_heat requires 'vessel'")
            if self.heat_level is None:
                raise ValueError("set_heat requires 'heat_level'")
        elif t == "cook":
            if not self.vessel:
                raise ValueError("cook requires 'vessel'")
            if self.duration_minutes is None:
                raise ValueError("cook requires 'duration_minutes'")
        elif t == "stir":
            if not self.vessel:
                raise ValueError("stir requires 'vessel'")
        elif t == "chop":
            if not self.ingredient:
                raise ValueError("chop requires 'ingredient'")
            if self.chop_style is None:
                raise ValueError("chop requires 'chop_style'")
        elif t == "mix":
            if not self.vessel:
                raise ValueError("mix requires 'vessel'")
        elif t == "transfer":
            if not self.from_vessel:
                raise ValueError("transfer requires 'from_vessel'")
            if not self.to_vessel:
                raise ValueError("transfer requires 'to_vessel'")
        elif t == "serve":
            if not self.vessel:
                raise ValueError("serve requires 'vessel'")
        elif t == "check_status":
            if not self.vessel:
                raise ValueError("check_status requires 'vessel'")
        elif t == "wait":
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
