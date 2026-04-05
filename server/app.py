"""
FastAPI application for the Rasoi (Indian Cooking) Environment.

Endpoints:
    - POST /reset: Reset the environment
    - POST /step: Execute an action
    - GET /state: Get current environment state
    - GET /schema: Get action/observation schemas
    - WS /ws: WebSocket endpoint for persistent sessions
"""

try:
    from openenv.core.env_server.http_server import create_app
except Exception as e:  # pragma: no cover
    raise ImportError(
        "openenv is required for the web interface. Install dependencies with '\n    uv sync\n'"
    ) from e

try:
    from ..models import RasoiAction, RasoiObservation
    from .rasoi_env_environment import RasoiEnvironment
except (ImportError, ModuleNotFoundError):
    from models import RasoiAction, RasoiObservation
    from server.rasoi_env_environment import RasoiEnvironment


app = create_app(
    RasoiEnvironment,
    RasoiAction,
    RasoiObservation,
    env_name="rasoi_env",
    max_concurrent_envs=4,
)


def main(host: str = "0.0.0.0", port: int = 8000):
    """Entry point for uv run server."""
    import uvicorn

    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    main()
