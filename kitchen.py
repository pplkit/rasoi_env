"""Kitchen simulation engine — manages vessels, ingredients, time, and cooking state."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

try:
    from .models import ActionType, RasoiAction, HeatLevel
    from .recipes import Recipe, TaskConfig
except ImportError:
    from models import ActionType, RasoiAction, HeatLevel
    from recipes import Recipe, TaskConfig


@dataclass
class IngredientState:
    """Tracks the state of a single ingredient in a vessel."""
    name: str
    quantity: str
    prepared: str = "raw"  # raw, chopped, mixed, cooked, overcooked, burned
    chop_style: Optional[str] = None
    cook_time: float = 0.0  # minutes this ingredient has been cooking

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "quantity": self.quantity,
            "prepared": self.prepared,
            "chop_style": self.chop_style,
            "cook_time": round(self.cook_time, 1),
        }


@dataclass
class Vessel:
    """A cooking vessel (pan, pot, bowl, etc.)."""
    name: str
    vessel_type: str  # saucepan, pan, pot, bowl, cup, wok, cutting_board, plate
    contents: List[IngredientState] = field(default_factory=list)
    heat_level: str = "off"
    total_cook_time: float = 0.0

    # Vessel types that support heating
    HEATABLE = {"saucepan", "pan", "pot", "wok", "small_pan", "rice_pot"}

    @property
    def can_heat(self) -> bool:
        return self.vessel_type in self.HEATABLE

    def advance_time(self, minutes: float, cook_thresholds: Dict[str, Tuple[int, int, int]]) -> List[str]:
        """Advance time for this vessel. Returns list of state change messages."""
        if self.heat_level == "off" or not self.contents:
            return []

        messages = []
        # Heat multiplier: low=0.5x, medium=1x, high=1.5x
        multiplier = {"low": 0.5, "medium": 1.0, "high": 1.5}.get(self.heat_level, 1.0)
        effective_minutes = minutes * multiplier

        self.total_cook_time += minutes

        for ing in self.contents:
            ing.cook_time += effective_minutes
            thresholds = cook_thresholds.get(ing.name, (5, 15, 25))
            cooked_at, overcooked_at, burned_at = thresholds

            old_state = ing.prepared
            if ing.cook_time >= burned_at:
                ing.prepared = "burned"
            elif ing.cook_time >= overcooked_at:
                ing.prepared = "overcooked"
            elif ing.cook_time >= cooked_at:
                if ing.prepared in ("raw", "chopped", "mixed"):
                    ing.prepared = "cooked"

            if ing.prepared != old_state:
                if ing.prepared == "burned":
                    messages.append(f"WARNING: {ing.name} in {self.name} has BURNED!")
                elif ing.prepared == "overcooked":
                    messages.append(f"Caution: {ing.name} in {self.name} is getting overcooked.")
                elif ing.prepared == "cooked":
                    messages.append(f"{ing.name} in {self.name} is now properly cooked.")

        return messages

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "type": self.vessel_type,
            "contents": [c.to_dict() for c in self.contents],
            "heat_level": self.heat_level,
            "total_cook_time": round(self.total_cook_time, 1),
            "num_items": len(self.contents),
        }


class Kitchen:
    """The main kitchen simulation."""

    def __init__(self, task_config: TaskConfig):
        self.task_config = task_config
        self.vessels: Dict[str, Vessel] = {}
        self.pantry: Dict[str, str] = dict(task_config.pantry)
        self.current_time: float = 0.0
        self.completed_dishes: List[str] = []
        self.serve_times: Dict[str, float] = {}
        self.action_log: List[Dict[str, Any]] = []
        self.ingredients_used: List[str] = []  # track what was actually used

        # Build combined cook thresholds from all recipes
        self.cook_thresholds: Dict[str, Tuple[int, int, int]] = {}
        for recipe in task_config.recipes:
            self.cook_thresholds.update(recipe.cook_thresholds)

        # Initialize vessels
        for vessel_name in task_config.vessels:
            vtype = self._infer_vessel_type(vessel_name)
            self.vessels[vessel_name] = Vessel(name=vessel_name, vessel_type=vtype)

    def _infer_vessel_type(self, name: str) -> str:
        """Infer vessel type from name."""
        type_map = {
            "saucepan": "saucepan",
            "pan": "pan",
            "pot": "pot",
            "rice_pot": "rice_pot",
            "small_pan": "small_pan",
            "bowl": "bowl",
            "mixing_bowl": "bowl",
            "wet_bowl": "bowl",
            "cup": "cup",
            "wok": "wok",
            "cutting_board": "cutting_board",
            "plate": "plate",
        }
        return type_map.get(name, name)

    def execute(self, action: RasoiAction) -> str:
        """Execute an action and return feedback string."""
        self.action_log.append({
            "action_type": action.action_type.value,
            "time": self.current_time,
        })

        handler = {
            ActionType.ADD_INGREDIENT: self._add_ingredient,
            ActionType.SET_HEAT: self._set_heat,
            ActionType.COOK: self._cook,
            ActionType.STIR: self._stir,
            ActionType.CHOP: self._chop,
            ActionType.MIX: self._mix,
            ActionType.TRANSFER: self._transfer,
            ActionType.SERVE: self._serve,
            ActionType.CHECK_STATUS: self._check_status,
            ActionType.WAIT: self._wait,
        }.get(action.action_type)

        if handler is None:
            return f"Error: Unknown action type '{action.action_type}'"

        return handler(action)

    def _get_vessel(self, name: str) -> Optional[Vessel]:
        return self.vessels.get(name)

    def _add_ingredient(self, action: RasoiAction) -> str:
        vessel = self._get_vessel(action.vessel)
        if vessel is None:
            return f"Error: Vessel '{action.vessel}' not found. Available: {list(self.vessels.keys())}"

        ingredient = action.ingredient
        if ingredient not in self.pantry:
            return f"Error: '{ingredient}' not in pantry. Available: {list(self.pantry.keys())}"

        quantity = action.quantity or self.pantry[ingredient]
        self.ingredients_used.append(ingredient)

        ing_state = IngredientState(
            name=ingredient,
            quantity=quantity,
            prepared="raw",
        )

        # Check if ingredient was previously chopped (on cutting board)
        cutting_board = self._get_vessel("cutting_board")
        if cutting_board:
            for cb_ing in cutting_board.contents:
                if cb_ing.name == ingredient and cb_ing.prepared == "chopped":
                    ing_state.prepared = "chopped"
                    ing_state.chop_style = cb_ing.chop_style
                    cutting_board.contents.remove(cb_ing)
                    break

        vessel.contents.append(ing_state)
        return f"Added {quantity} of {ingredient} to {vessel.name}."

    def _set_heat(self, action: RasoiAction) -> str:
        vessel = self._get_vessel(action.vessel)
        if vessel is None:
            return f"Error: Vessel '{action.vessel}' not found."
        if not vessel.can_heat:
            return f"Error: {vessel.name} ({vessel.vessel_type}) cannot be heated."

        old_level = vessel.heat_level
        vessel.heat_level = action.heat_level.value
        return f"Set {vessel.name} heat from {old_level} to {vessel.heat_level}."

    def _cook(self, action: RasoiAction) -> str:
        vessel = self._get_vessel(action.vessel)
        if vessel is None:
            return f"Error: Vessel '{action.vessel}' not found."
        if not vessel.can_heat:
            return f"Error: {vessel.name} cannot be heated."
        if vessel.heat_level == "off":
            return f"Error: {vessel.name} heat is off. Set heat first."
        if not vessel.contents:
            return f"Error: {vessel.name} is empty."

        duration = action.duration_minutes
        messages = self._advance_all_time(duration)
        vessel_msgs = [m for m in messages if vessel.name in m]
        other_msgs = [m for m in messages if vessel.name not in m]

        feedback = f"Cooked {vessel.name} for {duration} min. Time is now {self.current_time:.0f} min."
        if vessel_msgs:
            feedback += " " + " ".join(vessel_msgs)
        if other_msgs:
            feedback += " [Other vessels: " + " ".join(other_msgs) + "]"
        return feedback

    def _stir(self, action: RasoiAction) -> str:
        vessel = self._get_vessel(action.vessel)
        if vessel is None:
            return f"Error: Vessel '{action.vessel}' not found."
        if not vessel.contents:
            return f"Error: {vessel.name} is empty, nothing to stir."
        return f"Stirred contents of {vessel.name}."

    def _chop(self, action: RasoiAction) -> str:
        ingredient = action.ingredient
        if ingredient not in self.pantry:
            return f"Error: '{ingredient}' not in pantry."

        # Place chopped ingredient on cutting board (create one if needed)
        if "cutting_board" not in self.vessels:
            self.vessels["cutting_board"] = Vessel(
                name="cutting_board", vessel_type="cutting_board"
            )

        cutting_board = self.vessels["cutting_board"]
        ing_state = IngredientState(
            name=ingredient,
            quantity=self.pantry[ingredient],
            prepared="chopped",
            chop_style=action.chop_style.value if action.chop_style else "dice",
        )
        cutting_board.contents.append(ing_state)
        self.ingredients_used.append(ingredient)
        style = action.chop_style.value if action.chop_style else "chopped"
        return f"Chopped {ingredient} ({style}). It's on the cutting board."

    def _mix(self, action: RasoiAction) -> str:
        vessel = self._get_vessel(action.vessel)
        if vessel is None:
            return f"Error: Vessel '{action.vessel}' not found."
        if len(vessel.contents) < 1:
            return f"Error: {vessel.name} needs at least 1 ingredient to mix."

        for ing in vessel.contents:
            if ing.prepared == "raw":
                ing.prepared = "mixed"
        return f"Mixed {len(vessel.contents)} ingredients in {vessel.name}."

    def _transfer(self, action: RasoiAction) -> str:
        from_v = self._get_vessel(action.from_vessel)
        to_v = self._get_vessel(action.to_vessel)
        if from_v is None:
            return f"Error: Source vessel '{action.from_vessel}' not found."
        if to_v is None:
            return f"Error: Destination vessel '{action.to_vessel}' not found."
        if not from_v.contents:
            return f"Error: {from_v.name} is empty."

        transferred = list(from_v.contents)
        to_v.contents.extend(transferred)
        from_v.contents.clear()
        names = [i.name for i in transferred]
        return f"Transferred {', '.join(names)} from {from_v.name} to {to_v.name}."

    def _serve(self, action: RasoiAction) -> str:
        vessel = self._get_vessel(action.vessel)
        if vessel is None:
            return f"Error: Vessel '{action.vessel}' not found."
        if not vessel.contents:
            return f"Error: {vessel.name} is empty, nothing to serve."

        dish_name = action.dish_name or self._infer_dish_name(vessel)
        if dish_name in self.completed_dishes:
            return f"Error: {dish_name} has already been served."

        # Check for burned contents
        burned = [i.name for i in vessel.contents if i.prepared == "burned"]
        if burned:
            self.completed_dishes.append(dish_name)
            self.serve_times[dish_name] = self.current_time
            return f"Served {dish_name} from {vessel.name}, but {', '.join(burned)} were BURNED!"

        self.completed_dishes.append(dish_name)
        self.serve_times[dish_name] = self.current_time
        # Turn off heat
        if vessel.can_heat:
            vessel.heat_level = "off"
        return f"Served {dish_name} from {vessel.name} at time {self.current_time:.0f} min!"

    def _check_status(self, action: RasoiAction) -> str:
        vessel = self._get_vessel(action.vessel)
        if vessel is None:
            return f"Error: Vessel '{action.vessel}' not found."

        if not vessel.contents:
            status = f"{vessel.name} is empty. Heat: {vessel.heat_level}."
        else:
            items = []
            for ing in vessel.contents:
                items.append(f"{ing.name} ({ing.prepared}, {ing.cook_time:.1f} min cooked)")
            status = (
                f"{vessel.name}: heat={vessel.heat_level}, "
                f"contents=[{', '.join(items)}]"
            )
        return status

    def _wait(self, action: RasoiAction) -> str:
        duration = action.duration_minutes
        messages = self._advance_all_time(duration)
        feedback = f"Waited {duration} min. Time is now {self.current_time:.0f} min."
        if messages:
            feedback += " " + " ".join(messages)
        return feedback

    def _advance_all_time(self, minutes: float) -> List[str]:
        """Advance global time — all heated vessels progress."""
        self.current_time += minutes
        all_messages = []
        for vessel in self.vessels.values():
            msgs = vessel.advance_time(minutes, self.cook_thresholds)
            all_messages.extend(msgs)
        return all_messages

    def _infer_dish_name(self, vessel: Vessel) -> str:
        """Try to infer dish name from vessel contents or recipe mapping."""
        # Map vessels to likely dishes
        vessel_dish_map = {
            "cup": "masala_chai",
            "saucepan": "masala_chai",
            "pan": "pancakes",
            "pot": "dal",
            "rice_pot": "jeera_rice",
            "wok": "aloo_gobi",
        }
        return vessel_dish_map.get(vessel.name, vessel.name)

    def has_burned_food(self) -> bool:
        """Check if any food in any vessel is burned."""
        for vessel in self.vessels.values():
            for ing in vessel.contents:
                if ing.prepared == "burned":
                    return True
        return False

    def all_dishes_served(self) -> bool:
        """Check if all expected dishes have been served."""
        expected = {r.dish_name for r in self.task_config.recipes}
        return expected.issubset(set(self.completed_dishes))

    def get_vessels_dict(self) -> Dict[str, Dict[str, Any]]:
        """Get serialized vessel states."""
        return {name: v.to_dict() for name, v in self.vessels.items()}

    def get_pantry_list(self) -> List[str]:
        """Get pantry as list of strings."""
        return [f"{name}: {qty}" for name, qty in self.pantry.items()]
