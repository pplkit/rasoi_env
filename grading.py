"""Deterministic graders for the cooking environment tasks."""

from __future__ import annotations

from typing import Dict, List, Optional, Set, Tuple

try:
    from .kitchen import Kitchen
    from .models import RasoiAction
    from .recipes import RecipeStep, TaskConfig
except ImportError:
    from kitchen import Kitchen
    from models import RasoiAction
    from recipes import RecipeStep, TaskConfig


class TaskGrader:
    """Grades agent performance on cooking tasks."""

    def __init__(self, task_config: TaskConfig):
        self.task_config = task_config
        self.matched_steps: List[int] = []  # indices of matched recipe steps
        self.total_steps = sum(len(r.steps) for r in task_config.recipes)
        self.substitutions_made: Set[str] = set()  # track correct substitutions
        self.forbidden_used: Set[str] = set()  # track forbidden ingredient usage
        self.burn_count: int = 0
        self._burned_already: Set[str] = set()
        self._step_map = self._build_step_map()

    def _build_step_map(self) -> List[Tuple[int, RecipeStep]]:
        """Flatten all recipe steps with global indices."""
        steps = []
        idx = 0
        for recipe in self.task_config.recipes:
            for step in recipe.steps:
                steps.append((idx, step))
                idx += 1
        return steps

    def grade_step(self, action: RasoiAction, kitchen: Kitchen) -> float:
        """Grade a single step. Returns step reward."""
        reward = 0.0

        # Check for correct substitutions (Task 2)
        if self.task_config.substitution_rules and action.action_type.value == "add_ingredient":
            ingredient = action.ingredient
            # Check if agent correctly used a substitute
            for original, substitute in self.task_config.substitution_rules.items():
                if ingredient == substitute:
                    self.substitutions_made.add(original)
                    reward += 0.2
                elif ingredient == original:
                    self.forbidden_used.add(original)
                    reward -= 0.05

        # Check for burned food
        for vessel in kitchen.vessels.values():
            for ing in vessel.contents:
                if ing.prepared == "burned" and ing.name not in self._burned_already:
                    self._burned_already.add(ing.name)
                    self.burn_count += 1
                    reward -= 0.1

        # Match action against unmatched recipe steps
        matched = self._match_step(action)
        if matched:
            reward += 0.1

        # Bonus for serving a dish
        if action.action_type.value == "serve":
            dish_name = action.dish_name or ""
            for recipe in self.task_config.recipes:
                if recipe.dish_name == dish_name or dish_name == "":
                    # Check if dish is reasonably complete
                    recipe_matched = sum(
                        1 for idx, _ in self._step_map
                        if idx in self.matched_steps
                    )
                    if recipe_matched > 0:
                        reward += 0.3
                    break

        return reward

    def _match_step(self, action: RasoiAction) -> bool:
        """Try to match action against an unmatched recipe step."""
        action_type = action.action_type.value

        for idx, step in self._step_map:
            if idx in self.matched_steps:
                continue
            if step.expected_action != action_type:
                continue

            # Check critical ordering
            if step.critical_order is not None:
                # All steps with lower critical_order must already be matched
                for other_idx, other_step in self._step_map:
                    if (
                        other_step.critical_order is not None
                        and other_step.critical_order < step.critical_order
                        and other_idx not in self.matched_steps
                    ):
                        # A prerequisite step hasn't been matched yet — skip
                        continue  # continue inner loop; but we need to break logic

                # Simplified: check if any prerequisite is unmatched
                prerequisites_met = True
                for other_idx, other_step in self._step_map:
                    if (
                        other_step.critical_order is not None
                        and other_step.critical_order < step.critical_order
                        and other_idx not in self.matched_steps
                    ):
                        prerequisites_met = False
                        break
                if not prerequisites_met:
                    continue

            # Check key parameters match
            params_match = True
            for key, expected_val in step.expected_params.items():
                actual_val = getattr(action, key, None)
                if actual_val is None:
                    params_match = False
                    break
                # Handle enum values
                actual_str = actual_val.value if hasattr(actual_val, "value") else str(actual_val)
                # Allow substitutions
                if actual_str != expected_val:
                    # Check if this is a valid substitution
                    is_substitution = False
                    if key == "ingredient":
                        for orig, sub in self.task_config.substitution_rules.items():
                            if expected_val == orig and actual_str == sub:
                                is_substitution = True
                                break
                            if expected_val == sub and actual_str == sub:
                                is_substitution = True
                                break
                    if not is_substitution:
                        params_match = False
                        break

            if params_match:
                self.matched_steps.append(idx)
                return True

        return False

    def grade_episode(self, kitchen: Kitchen) -> float:
        """Compute final normalized score (0.0 to 1.0)."""
        task_id = self.task_config.task_id

        if task_id == "task_1":
            return self._grade_task1(kitchen)
        elif task_id == "task_2":
            return self._grade_task2(kitchen)
        elif task_id == "task_3":
            return self._grade_task3(kitchen)
        return 0.0

    def _grade_task1(self, kitchen: Kitchen) -> float:
        """Task 1: Masala Chai — step completion + dish served."""
        step_score = len(self.matched_steps) / max(self.total_steps, 1)
        dish_served = 1.0 if "masala_chai" in kitchen.completed_dishes else 0.0

        # Penalty for burned items
        burn_penalty = min(self.burn_count * 0.1, 0.3)

        score = 0.7 * step_score + 0.3 * dish_served - burn_penalty
        return max(0.0, min(1.0, score))

    def _grade_task2(self, kitchen: Kitchen) -> float:
        """Task 2: Dairy-Free Pancakes — substitution + steps + dish."""
        # Substitution score
        total_subs = len(self.task_config.substitution_rules)
        correct_subs = len(self.substitutions_made)
        forbidden_penalty = len(self.forbidden_used) * 0.15
        substitution_score = max(0.0, (correct_subs / max(total_subs, 1)) - forbidden_penalty)

        # Step score
        step_score = len(self.matched_steps) / max(self.total_steps, 1)

        # Dish score
        dish_served = 1.0 if "pancakes" in kitchen.completed_dishes else 0.0
        burn_penalty = min(self.burn_count * 0.15, 0.3)

        score = 0.3 * substitution_score + 0.4 * step_score + 0.3 * dish_served - burn_penalty
        return max(0.0, min(1.0, score))

    def _grade_task3(self, kitchen: Kitchen) -> float:
        """Task 3: Indian Thali — dishes + timing + no burns."""
        expected_dishes = {"dal", "jeera_rice", "aloo_gobi"}
        served = set(kitchen.completed_dishes)

        # Per-dish score
        dish_scores = []
        for dish in expected_dishes:
            if dish in served:
                # Check if dish has burned contents
                dish_scores.append(1.0)
            else:
                dish_scores.append(0.0)
        avg_dish_score = sum(dish_scores) / len(dish_scores) if dish_scores else 0.0

        # Timing score
        timing_score = 0.0
        served_expected = served.intersection(expected_dishes)
        if len(served_expected) >= 2:
            times = [kitchen.serve_times[d] for d in served_expected]
            spread = max(times) - min(times)
            window = self.task_config.target_ready_window or 5
            if spread <= window:
                timing_score = 1.0
            elif spread <= window + 10:
                timing_score = max(0.0, 1.0 - (spread - window) / 10.0)

        # No burn score
        no_burn_score = 1.0 if self.burn_count == 0 else 0.0

        score = 0.5 * avg_dish_score + 0.3 * timing_score + 0.2 * no_burn_score
        return max(0.0, min(1.0, score))

