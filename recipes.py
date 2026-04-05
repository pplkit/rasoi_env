"""Recipe definitions and task configurations for the cooking environment."""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple


@dataclass
class RecipeStep:
    """A single step in a recipe."""
    instruction: str
    expected_action: str  # ActionType value
    expected_params: Dict[str, str]  # key params to match
    critical_order: Optional[int] = None  # if set, must come after lower-numbered steps
    cook_time: Optional[int] = None  # expected duration for cook/wait actions
    tolerance: int = 2  # minutes tolerance for timing


@dataclass
class Recipe:
    """A complete recipe definition."""
    name: str
    dish_name: str
    ingredients: Dict[str, str]  # ingredient -> quantity
    steps: List[RecipeStep] = field(default_factory=list)
    cook_thresholds: Dict[str, Tuple[int, int, int]] = field(default_factory=dict)
    # ingredient -> (cooked_min, overcooked_min, burned_min)


@dataclass
class TaskConfig:
    """Configuration for a single task."""
    task_id: str
    difficulty: str
    recipes: List[Recipe]
    dietary_constraints: List[str] = field(default_factory=list)
    substitution_rules: Dict[str, str] = field(default_factory=dict)
    pantry: Dict[str, str] = field(default_factory=dict)
    vessels: List[str] = field(default_factory=list)
    max_steps: int = 25
    target_ready_window: Optional[int] = None  # minutes, for multi-dish tasks


# =============================================================================
# TASK 1: Masala Chai (Easy)
# =============================================================================

CHAI_RECIPE = Recipe(
    name="Masala Chai",
    dish_name="masala_chai",
    ingredients={
        "water": "1 cup",
        "ginger": "1 inch piece",
        "cinnamon_stick": "1 piece",
        "cardamom": "3 pods",
        "cloves": "3 pieces",
        "tea_leaves": "2 tsp",
        "milk": "0.5 cup",
        "sugar": "2 tsp",
    },
    steps=[
        RecipeStep(
            instruction="Add water to saucepan",
            expected_action="add_ingredient",
            expected_params={"ingredient": "water", "vessel": "saucepan"},
            critical_order=1,
        ),
        RecipeStep(
            instruction="Add ginger to saucepan",
            expected_action="add_ingredient",
            expected_params={"ingredient": "ginger", "vessel": "saucepan"},
            critical_order=2,
        ),
        RecipeStep(
            instruction="Add cinnamon, cardamom, cloves to saucepan",
            expected_action="add_ingredient",
            expected_params={"ingredient": "cinnamon_stick", "vessel": "saucepan"},
            critical_order=2,
        ),
        RecipeStep(
            instruction="Add cardamom to saucepan",
            expected_action="add_ingredient",
            expected_params={"ingredient": "cardamom", "vessel": "saucepan"},
            critical_order=2,
        ),
        RecipeStep(
            instruction="Add cloves to saucepan",
            expected_action="add_ingredient",
            expected_params={"ingredient": "cloves", "vessel": "saucepan"},
            critical_order=2,
        ),
        RecipeStep(
            instruction="Set heat to medium-high and boil water with spices",
            expected_action="set_heat",
            expected_params={"vessel": "saucepan", "heat_level": "high"},
            critical_order=3,
        ),
        RecipeStep(
            instruction="Boil/steep spices for 5-7 minutes",
            expected_action="cook",
            expected_params={"vessel": "saucepan"},
            critical_order=4,
            cook_time=5,
            tolerance=3,
        ),
        RecipeStep(
            instruction="Add tea leaves",
            expected_action="add_ingredient",
            expected_params={"ingredient": "tea_leaves", "vessel": "saucepan"},
            critical_order=5,
        ),
        RecipeStep(
            instruction="Steep tea for 1 minute",
            expected_action="cook",
            expected_params={"vessel": "saucepan"},
            critical_order=6,
            cook_time=1,
            tolerance=1,
        ),
        RecipeStep(
            instruction="Add milk",
            expected_action="add_ingredient",
            expected_params={"ingredient": "milk", "vessel": "saucepan"},
            critical_order=7,
        ),
        RecipeStep(
            instruction="Simmer with milk for 5 minutes",
            expected_action="cook",
            expected_params={"vessel": "saucepan"},
            critical_order=8,
            cook_time=5,
            tolerance=2,
        ),
        RecipeStep(
            instruction="Turn off heat",
            expected_action="set_heat",
            expected_params={"vessel": "saucepan", "heat_level": "off"},
            critical_order=9,
        ),
        RecipeStep(
            instruction="Add sugar",
            expected_action="add_ingredient",
            expected_params={"ingredient": "sugar", "vessel": "saucepan"},
        ),
        RecipeStep(
            instruction="Transfer chai to cup (strain)",
            expected_action="transfer",
            expected_params={"from_vessel": "saucepan", "to_vessel": "cup"},
            critical_order=10,
        ),
        RecipeStep(
            instruction="Serve the chai",
            expected_action="serve",
            expected_params={"vessel": "cup"},
            critical_order=11,
        ),
    ],
    cook_thresholds={
        # (cooked_min, overcooked_min, burned_min)
        # Note: effective cook time = minutes * heat_multiplier (high=1.5x, medium=1x, low=0.5x)
        "tea_leaves": (1, 8, 15),
        "milk": (5, 12, 20),
        "ginger": (5, 20, 35),
        "cinnamon_stick": (3, 25, 40),
        "cardamom": (3, 25, 40),
        "cloves": (3, 25, 40),
        "water": (1, 999, 999),  # water doesn't really burn
        "sugar": (1, 999, 999),
    },
)

TASK_1 = TaskConfig(
    task_id="task_1",
    difficulty="easy",
    recipes=[CHAI_RECIPE],
    pantry={
        "water": "2 cups",
        "ginger": "1 piece",
        "cinnamon_stick": "2 pieces",
        "cardamom": "5 pods",
        "cloves": "5 pieces",
        "tea_leaves": "4 tsp",
        "milk": "1 cup",
        "sugar": "4 tsp",
    },
    vessels=["saucepan", "cup"],
    max_steps=20,
)


# =============================================================================
# TASK 2: Dairy-Free Pancakes (Medium)
# =============================================================================

PANCAKE_RECIPE = Recipe(
    name="Dairy-Free Pancakes",
    dish_name="pancakes",
    ingredients={
        "flour": "2 cups",
        "sugar": "2 tbsp",
        "baking_powder": "2 tsp",
        "oat_milk": "1.5 cups",
        "eggs": "2",
        "coconut_oil": "3 tbsp",
        "salt": "0.5 tsp",
    },
    steps=[
        # Dry ingredients
        RecipeStep(
            instruction="Add flour to mixing bowl",
            expected_action="add_ingredient",
            expected_params={"ingredient": "flour", "vessel": "mixing_bowl"},
            critical_order=1,
        ),
        RecipeStep(
            instruction="Add sugar to mixing bowl",
            expected_action="add_ingredient",
            expected_params={"ingredient": "sugar", "vessel": "mixing_bowl"},
            critical_order=1,
        ),
        RecipeStep(
            instruction="Add baking powder to mixing bowl",
            expected_action="add_ingredient",
            expected_params={"ingredient": "baking_powder", "vessel": "mixing_bowl"},
            critical_order=1,
        ),
        RecipeStep(
            instruction="Add salt to mixing bowl",
            expected_action="add_ingredient",
            expected_params={"ingredient": "salt", "vessel": "mixing_bowl"},
            critical_order=1,
        ),
        RecipeStep(
            instruction="Mix dry ingredients",
            expected_action="mix",
            expected_params={"vessel": "mixing_bowl"},
            critical_order=2,
        ),
        # Wet ingredients
        RecipeStep(
            instruction="Add oat milk to second bowl",
            expected_action="add_ingredient",
            expected_params={"ingredient": "oat_milk", "vessel": "wet_bowl"},
            critical_order=3,
        ),
        RecipeStep(
            instruction="Add eggs to second bowl",
            expected_action="add_ingredient",
            expected_params={"ingredient": "eggs", "vessel": "wet_bowl"},
            critical_order=3,
        ),
        RecipeStep(
            instruction="Add coconut oil to second bowl",
            expected_action="add_ingredient",
            expected_params={"ingredient": "coconut_oil", "vessel": "wet_bowl"},
            critical_order=3,
        ),
        RecipeStep(
            instruction="Mix wet ingredients",
            expected_action="mix",
            expected_params={"vessel": "wet_bowl"},
            critical_order=4,
        ),
        # Combine
        RecipeStep(
            instruction="Transfer wet to dry bowl",
            expected_action="transfer",
            expected_params={"from_vessel": "wet_bowl", "to_vessel": "mixing_bowl"},
            critical_order=5,
        ),
        RecipeStep(
            instruction="Mix combined batter",
            expected_action="mix",
            expected_params={"vessel": "mixing_bowl"},
            critical_order=6,
        ),
        # Cook
        RecipeStep(
            instruction="Set heat on pan to medium",
            expected_action="set_heat",
            expected_params={"vessel": "pan", "heat_level": "medium"},
            critical_order=7,
        ),
        RecipeStep(
            instruction="Add coconut oil to pan",
            expected_action="add_ingredient",
            expected_params={"ingredient": "coconut_oil", "vessel": "pan"},
            critical_order=8,
        ),
        RecipeStep(
            instruction="Heat oil for 1 minute",
            expected_action="cook",
            expected_params={"vessel": "pan"},
            critical_order=9,
            cook_time=1,
            tolerance=1,
        ),
        RecipeStep(
            instruction="Transfer batter to pan",
            expected_action="transfer",
            expected_params={"from_vessel": "mixing_bowl", "to_vessel": "pan"},
            critical_order=10,
        ),
        RecipeStep(
            instruction="Cook first side for 3 minutes",
            expected_action="cook",
            expected_params={"vessel": "pan"},
            critical_order=11,
            cook_time=3,
            tolerance=1,
        ),
        RecipeStep(
            instruction="Flip pancake (stir)",
            expected_action="stir",
            expected_params={"vessel": "pan"},
            critical_order=12,
        ),
        RecipeStep(
            instruction="Cook second side for 2 minutes",
            expected_action="cook",
            expected_params={"vessel": "pan"},
            critical_order=13,
            cook_time=2,
            tolerance=1,
        ),
        RecipeStep(
            instruction="Serve pancakes",
            expected_action="serve",
            expected_params={"vessel": "pan"},
            critical_order=14,
        ),
    ],
    cook_thresholds={
        "flour": (3, 6, 10),
        "oat_milk": (3, 6, 10),
        "eggs": (3, 6, 10),
        "coconut_oil": (1, 4, 7),
        "sugar": (3, 8, 12),
        "baking_powder": (3, 8, 12),
        "salt": (3, 999, 999),
    },
)

TASK_2 = TaskConfig(
    task_id="task_2",
    difficulty="medium",
    recipes=[PANCAKE_RECIPE],
    dietary_constraints=["dairy-free"],
    substitution_rules={"milk": "oat_milk", "butter": "coconut_oil"},
    pantry={
        "flour": "4 cups",
        "sugar": "0.5 cup",
        "baking_powder": "4 tsp",
        "salt": "1 tsp",
        # Both dairy and non-dairy options — agent must choose correctly
        "milk": "2 cups",
        "oat_milk": "2 cups",
        "butter": "4 tbsp",
        "coconut_oil": "6 tbsp",
        "eggs": "4",
    },
    vessels=["mixing_bowl", "wet_bowl", "pan", "plate"],
    max_steps=35,
)


# =============================================================================
# TASK 3: Indian Thali (Hard)
# =============================================================================

DAL_RECIPE = Recipe(
    name="Moong Dal",
    dish_name="dal",
    ingredients={
        "moong_dal": "1 cup",
        "water": "3 cups",
        "turmeric": "0.5 tsp",
        "salt": "0.5 tsp",
        "ghee": "1 tbsp",
        "cumin_seeds": "1 tsp",
        "garlic": "2 cloves",
        "green_chilies": "2",
        "cilantro": "2 tbsp",
    },
    steps=[
        RecipeStep(
            instruction="Add moong dal to pot",
            expected_action="add_ingredient",
            expected_params={"ingredient": "moong_dal", "vessel": "pot"},
            critical_order=1,
        ),
        RecipeStep(
            instruction="Add water to pot",
            expected_action="add_ingredient",
            expected_params={"ingredient": "water", "vessel": "pot"},
            critical_order=1,
        ),
        RecipeStep(
            instruction="Add turmeric to pot",
            expected_action="add_ingredient",
            expected_params={"ingredient": "turmeric", "vessel": "pot"},
            critical_order=1,
        ),
        RecipeStep(
            instruction="Add salt to pot",
            expected_action="add_ingredient",
            expected_params={"ingredient": "salt", "vessel": "pot"},
            critical_order=1,
        ),
        RecipeStep(
            instruction="Set heat on pot to high",
            expected_action="set_heat",
            expected_params={"vessel": "pot", "heat_level": "high"},
            critical_order=2,
        ),
        RecipeStep(
            instruction="Cook dal for 15 minutes",
            expected_action="cook",
            expected_params={"vessel": "pot"},
            critical_order=3,
            cook_time=15,
            tolerance=3,
        ),
        RecipeStep(
            instruction="Reduce heat on pot",
            expected_action="set_heat",
            expected_params={"vessel": "pot", "heat_level": "low"},
            critical_order=4,
        ),
        # Tadka
        RecipeStep(
            instruction="Add ghee to small_pan",
            expected_action="add_ingredient",
            expected_params={"ingredient": "ghee", "vessel": "small_pan"},
            critical_order=5,
        ),
        RecipeStep(
            instruction="Set heat on small pan to medium",
            expected_action="set_heat",
            expected_params={"vessel": "small_pan", "heat_level": "medium"},
            critical_order=6,
        ),
        RecipeStep(
            instruction="Add cumin seeds to small pan",
            expected_action="add_ingredient",
            expected_params={"ingredient": "cumin_seeds", "vessel": "small_pan"},
            critical_order=7,
        ),
        RecipeStep(
            instruction="Add garlic to small pan",
            expected_action="add_ingredient",
            expected_params={"ingredient": "garlic", "vessel": "small_pan"},
            critical_order=7,
        ),
        RecipeStep(
            instruction="Add green chilies to small pan",
            expected_action="add_ingredient",
            expected_params={"ingredient": "green_chilies", "vessel": "small_pan"},
            critical_order=7,
        ),
        RecipeStep(
            instruction="Cook tadka for 2 minutes",
            expected_action="cook",
            expected_params={"vessel": "small_pan"},
            critical_order=8,
            cook_time=2,
            tolerance=1,
        ),
        RecipeStep(
            instruction="Transfer tadka to pot",
            expected_action="transfer",
            expected_params={"from_vessel": "small_pan", "to_vessel": "pot"},
            critical_order=9,
        ),
        RecipeStep(
            instruction="Stir dal",
            expected_action="stir",
            expected_params={"vessel": "pot"},
            critical_order=10,
        ),
        RecipeStep(
            instruction="Serve dal",
            expected_action="serve",
            expected_params={"vessel": "pot"},
            critical_order=11,
        ),
    ],
    cook_thresholds={
        "moong_dal": (15, 20, 28),
        "water": (1, 999, 999),
        "turmeric": (1, 999, 999),
        "salt": (1, 999, 999),
        "ghee": (1, 3, 5),
        "cumin_seeds": (1, 3, 5),
        "garlic": (1, 3, 5),
        "green_chilies": (1, 4, 6),
        "cilantro": (1, 999, 999),
    },
)

RICE_RECIPE = Recipe(
    name="Jeera Rice",
    dish_name="jeera_rice",
    ingredients={
        "rice": "1 cup",
        "water": "1.5 cups",
        "oil": "1 tbsp",
        "cumin_seeds": "1 tsp",
        "salt": "0.5 tsp",
    },
    steps=[
        RecipeStep(
            instruction="Add oil to rice_pot",
            expected_action="add_ingredient",
            expected_params={"ingredient": "oil", "vessel": "rice_pot"},
            critical_order=1,
        ),
        RecipeStep(
            instruction="Set heat on rice pot to medium",
            expected_action="set_heat",
            expected_params={"vessel": "rice_pot", "heat_level": "medium"},
            critical_order=2,
        ),
        RecipeStep(
            instruction="Add cumin seeds to rice pot",
            expected_action="add_ingredient",
            expected_params={"ingredient": "cumin_seeds", "vessel": "rice_pot"},
            critical_order=3,
        ),
        RecipeStep(
            instruction="Cook cumin for 1 minute to bloom",
            expected_action="cook",
            expected_params={"vessel": "rice_pot"},
            critical_order=4,
            cook_time=1,
            tolerance=1,
        ),
        RecipeStep(
            instruction="Add rice to rice pot",
            expected_action="add_ingredient",
            expected_params={"ingredient": "rice", "vessel": "rice_pot"},
            critical_order=5,
        ),
        RecipeStep(
            instruction="Add water to rice pot",
            expected_action="add_ingredient",
            expected_params={"ingredient": "water", "vessel": "rice_pot"},
            critical_order=5,
        ),
        RecipeStep(
            instruction="Add salt to rice pot",
            expected_action="add_ingredient",
            expected_params={"ingredient": "salt", "vessel": "rice_pot"},
            critical_order=5,
        ),
        RecipeStep(
            instruction="Set heat to low and cook covered for 12 minutes",
            expected_action="set_heat",
            expected_params={"vessel": "rice_pot", "heat_level": "low"},
            critical_order=6,
        ),
        RecipeStep(
            instruction="Cook rice for 12 minutes",
            expected_action="cook",
            expected_params={"vessel": "rice_pot"},
            critical_order=7,
            cook_time=12,
            tolerance=2,
        ),
        RecipeStep(
            instruction="Turn off heat",
            expected_action="set_heat",
            expected_params={"vessel": "rice_pot", "heat_level": "off"},
            critical_order=8,
        ),
        RecipeStep(
            instruction="Stir/fluff rice",
            expected_action="stir",
            expected_params={"vessel": "rice_pot"},
            critical_order=9,
        ),
        RecipeStep(
            instruction="Serve rice",
            expected_action="serve",
            expected_params={"vessel": "rice_pot"},
            critical_order=10,
        ),
    ],
    cook_thresholds={
        "rice": (12, 18, 25),
        "water": (1, 999, 999),
        "oil": (1, 5, 8),
        "cumin_seeds": (1, 3, 5),
        "salt": (1, 999, 999),
    },
)

SABZI_RECIPE = Recipe(
    name="Aloo Gobi Sabzi",
    dish_name="aloo_gobi",
    ingredients={
        "oil": "2 tbsp",
        "mustard_seeds": "0.5 tsp",
        "cumin_seeds": "1 tsp",
        "onion": "1",
        "potato": "2",
        "cauliflower": "2 cups",
        "turmeric": "0.5 tsp",
        "red_chili_powder": "0.5 tsp",
        "salt": "0.5 tsp",
        "cilantro": "2 tbsp",
    },
    steps=[
        RecipeStep(
            instruction="Chop potato into cubes",
            expected_action="chop",
            expected_params={"ingredient": "potato", "chop_style": "dice"},
            critical_order=1,
        ),
        RecipeStep(
            instruction="Chop cauliflower into florets",
            expected_action="chop",
            expected_params={"ingredient": "cauliflower", "chop_style": "dice"},
            critical_order=1,
        ),
        RecipeStep(
            instruction="Chop onion",
            expected_action="chop",
            expected_params={"ingredient": "onion", "chop_style": "dice"},
            critical_order=1,
        ),
        RecipeStep(
            instruction="Add oil to wok",
            expected_action="add_ingredient",
            expected_params={"ingredient": "oil", "vessel": "wok"},
            critical_order=2,
        ),
        RecipeStep(
            instruction="Set heat on wok to medium-high",
            expected_action="set_heat",
            expected_params={"vessel": "wok", "heat_level": "high"},
            critical_order=3,
        ),
        RecipeStep(
            instruction="Add mustard seeds to wok",
            expected_action="add_ingredient",
            expected_params={"ingredient": "mustard_seeds", "vessel": "wok"},
            critical_order=4,
        ),
        RecipeStep(
            instruction="Add cumin seeds to wok",
            expected_action="add_ingredient",
            expected_params={"ingredient": "cumin_seeds", "vessel": "wok"},
            critical_order=4,
        ),
        RecipeStep(
            instruction="Cook spices for 1 minute to bloom",
            expected_action="cook",
            expected_params={"vessel": "wok"},
            critical_order=5,
            cook_time=1,
            tolerance=1,
        ),
        RecipeStep(
            instruction="Add chopped onion to wok",
            expected_action="add_ingredient",
            expected_params={"ingredient": "onion", "vessel": "wok"},
            critical_order=6,
        ),
        RecipeStep(
            instruction="Add potato to wok",
            expected_action="add_ingredient",
            expected_params={"ingredient": "potato", "vessel": "wok"},
            critical_order=6,
        ),
        RecipeStep(
            instruction="Add cauliflower to wok",
            expected_action="add_ingredient",
            expected_params={"ingredient": "cauliflower", "vessel": "wok"},
            critical_order=6,
        ),
        RecipeStep(
            instruction="Add turmeric",
            expected_action="add_ingredient",
            expected_params={"ingredient": "turmeric", "vessel": "wok"},
            critical_order=7,
        ),
        RecipeStep(
            instruction="Add red chili powder",
            expected_action="add_ingredient",
            expected_params={"ingredient": "red_chili_powder", "vessel": "wok"},
            critical_order=7,
        ),
        RecipeStep(
            instruction="Add salt",
            expected_action="add_ingredient",
            expected_params={"ingredient": "salt", "vessel": "wok"},
            critical_order=7,
        ),
        RecipeStep(
            instruction="Stir everything together",
            expected_action="stir",
            expected_params={"vessel": "wok"},
            critical_order=8,
        ),
        RecipeStep(
            instruction="Reduce heat to medium-low",
            expected_action="set_heat",
            expected_params={"vessel": "wok", "heat_level": "medium"},
            critical_order=9,
        ),
        RecipeStep(
            instruction="Cook covered for 15 minutes",
            expected_action="cook",
            expected_params={"vessel": "wok"},
            critical_order=10,
            cook_time=15,
            tolerance=3,
        ),
        RecipeStep(
            instruction="Stir occasionally",
            expected_action="stir",
            expected_params={"vessel": "wok"},
            critical_order=11,
        ),
        RecipeStep(
            instruction="Serve aloo gobi",
            expected_action="serve",
            expected_params={"vessel": "wok"},
            critical_order=12,
        ),
    ],
    cook_thresholds={
        "oil": (1, 5, 8),
        "mustard_seeds": (1, 3, 5),
        "cumin_seeds": (1, 3, 5),
        "onion": (3, 10, 15),
        "potato": (10, 18, 25),
        "cauliflower": (8, 15, 22),
        "turmeric": (1, 999, 999),
        "red_chili_powder": (1, 999, 999),
        "salt": (1, 999, 999),
        "cilantro": (1, 999, 999),
    },
)

TASK_3 = TaskConfig(
    task_id="task_3",
    difficulty="hard",
    recipes=[DAL_RECIPE, RICE_RECIPE, SABZI_RECIPE],
    pantry={
        "moong_dal": "2 cups",
        "water": "10 cups",
        "turmeric": "2 tsp",
        "salt": "2 tsp",
        "ghee": "3 tbsp",
        "cumin_seeds": "3 tsp",
        "garlic": "4 cloves",
        "green_chilies": "4",
        "cilantro": "4 tbsp",
        "rice": "2 cups",
        "oil": "4 tbsp",
        "mustard_seeds": "1 tsp",
        "onion": "2",
        "potato": "4",
        "cauliflower": "4 cups",
        "red_chili_powder": "1 tsp",
    },
    vessels=["pot", "rice_pot", "small_pan", "wok", "cutting_board"],
    max_steps=50,
    target_ready_window=5,  # all dishes served within 5 minutes
)


# =============================================================================
# Task registry
# =============================================================================

TASKS: Dict[str, TaskConfig] = {
    "task_1": TASK_1,
    "task_2": TASK_2,
    "task_3": TASK_3,
}


def get_task_config(task_id: str) -> TaskConfig:
    if task_id not in TASKS:
        raise ValueError(f"Unknown task: {task_id}. Available: {list(TASKS.keys())}")
    return TASKS[task_id]


def get_recipe_text(task_config: TaskConfig) -> str:
    """Generate human-readable recipe text for the agent."""
    lines = []
    for recipe in task_config.recipes:
        lines.append(f"=== {recipe.name} ===")
        lines.append(f"Dish name: {recipe.dish_name}")
        lines.append("Ingredients:")
        for ing, qty in recipe.ingredients.items():
            lines.append(f"  - {ing}: {qty}")
        lines.append("Steps:")
        for i, step in enumerate(recipe.steps, 1):
            lines.append(f"  {i}. {step.instruction}")
        lines.append("")

    if task_config.dietary_constraints:
        lines.append(f"DIETARY CONSTRAINTS: {', '.join(task_config.dietary_constraints)}")
        if task_config.substitution_rules:
            lines.append("Required substitutions:")
            for orig, sub in task_config.substitution_rules.items():
                lines.append(f"  - Use {sub} instead of {orig}")
        lines.append("")

    if task_config.target_ready_window is not None:
        lines.append(
            f"TIMING: All dishes must be served within {task_config.target_ready_window} "
            f"minutes of each other!"
        )

    return "\n".join(lines)
