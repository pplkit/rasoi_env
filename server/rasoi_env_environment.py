"""
Rasoi Environment Implementation.

A virtual Indian kitchen where AI agents learn to cook authentic recipes
like Masala Chai, Dairy-Free Pancakes, and Indian Thali meals.
"""

from typing import Any, Optional
from uuid import uuid4

from openenv.core.env_server.interfaces import Environment
from openenv.core.env_server.types import EnvironmentMetadata

try:
    from ..grading import TaskGrader
    from ..kitchen import Kitchen
    from ..models import RasoiAction, RasoiObservation, RasoiState
    from ..recipes import get_recipe_text, get_task_config
except ImportError:
    from grading import TaskGrader
    from kitchen import Kitchen
    from models import RasoiAction, RasoiObservation, RasoiState
    from recipes import get_recipe_text, get_task_config


class RasoiEnvironment(Environment):
    """A virtual Indian kitchen where agents learn to cook authentic recipes."""

    SUPPORTS_CONCURRENT_SESSIONS: bool = True

    def __init__(self):
        super().__init__()
        self._kitchen: Optional[Kitchen] = None
        self._grader: Optional[TaskGrader] = None
        self._task_config = None
        self._state = RasoiState(episode_id=str(uuid4()), step_count=0)
        self._cumulative_reward: float = 0.0
        self._rewards: list[float] = []

    def reset(
        self,
        seed: Optional[int] = None,
        episode_id: Optional[str] = None,
        **kwargs: Any,
    ) -> RasoiObservation:
        """Reset the environment for a new episode."""
        task_id = kwargs.get("task_id", "task_1")
        self._task_config = get_task_config(task_id)
        self._kitchen = Kitchen(self._task_config)
        self._grader = TaskGrader(self._task_config)
        self._cumulative_reward = 0.0
        self._rewards = []

        self._state = RasoiState(
            episode_id=episode_id or str(uuid4()),
            step_count=0,
            task_id=task_id,
            current_time=0.0,
            completed_dishes=[],
            score=0.0,
            cumulative_reward=0.0,
        )

        recipe_text = get_recipe_text(self._task_config)

        return RasoiObservation(
            vessels=self._kitchen.get_vessels_dict(),
            available_ingredients=self._kitchen.get_pantry_list(),
            recipe=recipe_text,
            current_time=0.0,
            dietary_constraints=self._task_config.dietary_constraints,
            feedback="Kitchen is ready. Follow the recipe to cook!",
            completed_dishes=[],
            score=0.0,
            task_id=task_id,
            done=False,
            reward=0.0,
        )

    def step(
        self,
        action: RasoiAction,
        timeout_s: Optional[float] = None,
        **kwargs: Any,
    ) -> RasoiObservation:
        """Execute one cooking action."""
        if self._kitchen is None or self._grader is None:
            return RasoiObservation(
                feedback="Error: Environment not initialized. Call reset() first.",
                done=True,
                reward=0.0,
            )

        self._state.step_count += 1

        feedback = self._kitchen.execute(action)
        step_reward = self._grader.grade_step(action, self._kitchen)
        self._cumulative_reward += step_reward
        self._rewards.append(step_reward)

        done = False
        final_score = 0.0

        if self._kitchen.all_dishes_served():
            done = True
            final_score = self._grader.grade_episode(self._kitchen)
            feedback += f" All dishes served! Final score: {final_score:.2f}"
        elif self._state.step_count >= self._task_config.max_steps:
            done = True
            final_score = self._grader.grade_episode(self._kitchen)
            feedback += f" Max steps reached. Final score: {final_score:.2f}"

        self._state.current_time = self._kitchen.current_time
        self._state.completed_dishes = list(self._kitchen.completed_dishes)
        self._state.score = final_score if done else self._cumulative_reward
        self._state.cumulative_reward = self._cumulative_reward
        self._state.vessels_summary = self._kitchen.get_vessels_dict()

        return RasoiObservation(
            vessels=self._kitchen.get_vessels_dict(),
            available_ingredients=self._kitchen.get_pantry_list(),
            recipe=get_recipe_text(self._task_config),
            current_time=self._kitchen.current_time,
            dietary_constraints=self._task_config.dietary_constraints,
            feedback=feedback,
            completed_dishes=list(self._kitchen.completed_dishes),
            score=final_score if done else self._cumulative_reward,
            task_id=self._task_config.task_id,
            done=done,
            reward=step_reward,
        )

    @property
    def state(self) -> RasoiState:
        """Return current environment state."""
        return self._state

    def get_metadata(self) -> EnvironmentMetadata:
        return EnvironmentMetadata(
            name="Rasoi - Indian Cooking Assistant",
            description=(
                "A virtual Indian kitchen where AI agents learn to cook authentic recipes "
                "like Masala Chai, Dairy-Free Pancakes, and Indian Thali meals. "
                "Tests recipe following, ingredient substitution, and parallel cooking management."
            ),
            version="1.0.0",
        )
