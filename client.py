"""Rasoi Environment Client."""

from typing import Dict

from openenv.core import EnvClient
from openenv.core.client_types import StepResult
from openenv.core.env_server.types import State

from .models import RasoiAction, RasoiObservation, RasoiState


class RasoiEnv(EnvClient[RasoiAction, RasoiObservation, RasoiState]):
    """Client for interacting with the Rasoi cooking environment."""

    def _step_payload(self, action: RasoiAction) -> Dict:
        return action.model_dump(exclude_none=True)

    def _parse_result(self, payload: Dict) -> StepResult[RasoiObservation]:
        obs_data = payload.get("observation", payload)
        observation = RasoiObservation(
            vessels=obs_data.get("vessels", {}),
            available_ingredients=obs_data.get("available_ingredients", []),
            recipe=obs_data.get("recipe", ""),
            current_time=obs_data.get("current_time", 0.0),
            dietary_constraints=obs_data.get("dietary_constraints", []),
            feedback=obs_data.get("feedback", ""),
            completed_dishes=obs_data.get("completed_dishes", []),
            score=obs_data.get("score", 0.0),
            task_id=obs_data.get("task_id", "task_1"),
            done=payload.get("done", obs_data.get("done", False)),
            reward=payload.get("reward", obs_data.get("reward")),
            metadata=obs_data.get("metadata", {}),
        )
        return StepResult(
            observation=observation,
            reward=payload.get("reward", obs_data.get("reward")),
            done=payload.get("done", obs_data.get("done", False)),
        )

    def _parse_state(self, payload: Dict) -> RasoiState:
        return RasoiState(
            episode_id=payload.get("episode_id"),
            step_count=payload.get("step_count", 0),
            task_id=payload.get("task_id", "task_1"),
            current_time=payload.get("current_time", 0.0),
            completed_dishes=payload.get("completed_dishes", []),
            score=payload.get("score", 0.0),
            cumulative_reward=payload.get("cumulative_reward", 0.0),
        )
