"""
Inference Script — Rasoi (Indian Cooking Assistant)
===================================
MANDATORY
- Before submitting, ensure the following variables are defined in your environment configuration:
    API_BASE_URL   The API endpoint for the LLM.
    MODEL_NAME     The model identifier to use for inference.
    HF_TOKEN       Your Hugging Face / API key.

STDOUT FORMAT
- The script must emit exactly three line types to stdout, in this order:
    [START] task=<task_name> env=<benchmark> model=<model_name>
    [STEP]  step=<n> action=<action_str> reward=<0.00> done=<true|false> error=<msg|null>
    [END]   success=<true|false> steps=<n> score=<score> rewards=<r1,r2,...,rn>
"""

import json
import os
import sys
import textwrap
from typing import Any, Dict, List, Optional

from openai import OpenAI

from server.rasoi_env_environment import RasoiEnvironment
from models import RasoiAction

API_KEY = os.getenv("HF_TOKEN") or os.getenv("API_KEY")
API_BASE_URL = os.getenv("API_BASE_URL", "https://router.huggingface.co/v1")
MODEL_NAME = os.getenv("MODEL_NAME", "Qwen/Qwen2.5-72B-Instruct")
LOCAL_IMAGE_NAME = os.getenv("LOCAL_IMAGE_NAME")  # Optional: for from_docker_image()
BENCHMARK = "rasoi_env"

TASKS = ["task_1", "task_2", "task_3"]
MAX_STEPS_PER_TASK = {"task_1": 20, "task_2": 35, "task_3": 50}
TEMPERATURE = 0.7
MAX_TOKENS = 500

SYSTEM_PROMPT = textwrap.dedent("""\
You are an AI chef interacting with a virtual kitchen environment. You must cook dishes by
issuing JSON actions. Each action must be a valid JSON object with the following structure:

{
    "action_type": "<one of: add_ingredient, set_heat, cook, stir, chop, mix, transfer, serve, check_status, wait>",
    "ingredient": "<ingredient name>",       // for add_ingredient, chop
    "quantity": "<amount>",                   // for add_ingredient (optional)
    "vessel": "<vessel name>",               // for most actions
    "heat_level": "<off|low|medium|high>",   // for set_heat
    "duration_minutes": <integer>,           // for cook, wait
    "chop_style": "<dice|mince|slice|julienne>",  // for chop
    "from_vessel": "<source>",               // for transfer
    "to_vessel": "<destination>",            // for transfer
    "dish_name": "<name>"                    // for serve
}

Only include fields relevant to the action_type. Respond with ONLY the JSON action, no explanation.

IMPORTANT RULES:
- Time advances globally when you cook or wait. ALL heated vessels advance simultaneously.
- Food BURNS if cooked too long. Monitor cook times carefully.
- For dairy-free tasks, use substitutes (oat_milk instead of milk, coconut_oil instead of butter).
- For multi-dish tasks, stagger start times so dishes finish around the same time.
- Always set heat before cooking. Always add ingredients before cooking them.
""")


def log_start(task: str, env: str, model: str) -> None:
    print(f"[START] task={task} env={env} model={model}", flush=True)


def log_step(step: int, action: str, reward: float, done: bool, error: Optional[str]) -> None:
    error_val = error if error else "null"
    done_str = "true" if done else "false"
    print(
        f"[STEP] step={step} action={action} reward={reward:.2f} done={done_str} error={error_val}",
        flush=True,
    )


def log_end(success: bool, steps: int, score: float, rewards: List[float]) -> None:
    success_str = "true" if success else "false"
    rewards_str = ",".join(f"{r:.2f}" for r in rewards)
    print(
        f"[END] success={success_str} steps={steps} score={score:.2f} rewards={rewards_str}",
        flush=True,
    )


def obs_to_dict(obs) -> Dict[str, Any]:
    """Convert RasoiObservation to dict for formatting."""
    return {
        "vessels": obs.vessels,
        "available_ingredients": obs.available_ingredients,
        "recipe": obs.recipe,
        "current_time": obs.current_time,
        "dietary_constraints": obs.dietary_constraints,
        "feedback": obs.feedback,
        "completed_dishes": obs.completed_dishes,
        "score": obs.score,
        "task_id": obs.task_id,
        "done": obs.done,
        "reward": obs.reward,
    }


def format_observation(obs_dict: Dict[str, Any], task_id: str) -> str:
    """Format observation into a user message for the LLM."""
    lines = []
    lines.append(f"Task: {task_id}")
    lines.append(f"Time: {obs_dict.get('current_time', 0):.0f} minutes elapsed")
    lines.append(f"Feedback: {obs_dict.get('feedback', '')}")

    if obs_dict.get("dietary_constraints"):
        lines.append(f"Dietary constraints: {', '.join(obs_dict['dietary_constraints'])}")

    lines.append("")
    lines.append("=== Recipe ===")
    lines.append(obs_dict.get("recipe", ""))

    lines.append("")
    lines.append("=== Kitchen State ===")
    vessels = obs_dict.get("vessels", {})
    for vname, vstate in vessels.items():
        contents = vstate.get("contents", [])
        if contents:
            items = []
            for c in contents:
                items.append(f"{c['name']}({c['prepared']}, {c['cook_time']}min)")
            lines.append(
                f"  {vname}: heat={vstate.get('heat_level', 'off')}, "
                f"contents=[{', '.join(items)}]"
            )
        else:
            lines.append(f"  {vname}: empty, heat={vstate.get('heat_level', 'off')}")

    lines.append("")
    lines.append("=== Pantry ===")
    for item in obs_dict.get("available_ingredients", []):
        lines.append(f"  {item}")

    if obs_dict.get("completed_dishes"):
        lines.append(f"\nCompleted dishes: {', '.join(obs_dict['completed_dishes'])}")

    lines.append(f"\nScore so far: {obs_dict.get('score', 0):.2f}")
    lines.append("\nWhat is your next action? Respond with ONLY a JSON action object.")

    return "\n".join(lines)


def parse_llm_action(response_text: str) -> dict:
    """Parse the LLM response as a JSON action."""
    text = response_text.strip()
    if "```json" in text:
        text = text.split("```json")[1].split("```")[0].strip()
    elif "```" in text:
        text = text.split("```")[1].split("```")[0].strip()

    start = text.find("{")
    end = text.rfind("}") + 1
    if start >= 0 and end > start:
        text = text[start:end]

    return json.loads(text)


def run_task(client: OpenAI, task_id: str) -> float:
    """Run a single task and return the final score."""
    log_start(task=task_id, env=BENCHMARK, model=MODEL_NAME)

    env = RasoiEnvironment()
    obs = env.reset(task_id=task_id)
    obs_dict = obs_to_dict(obs)
    max_steps = MAX_STEPS_PER_TASK.get(task_id, 25)

    rewards: List[float] = []
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
    ]

    done = False
    step_num = 0
    score = 0.0

    while not done and step_num < max_steps:
        step_num += 1

        user_msg = format_observation(obs_dict, task_id)
        messages.append({"role": "user", "content": user_msg})

        if len(messages) > 20:
            messages = [messages[0]] + messages[-18:]

        try:
            completion = client.chat.completions.create(
                model=MODEL_NAME,
                messages=messages,
                temperature=TEMPERATURE,
                max_tokens=MAX_TOKENS,
            )
            response_text = completion.choices[0].message.content or ""
            messages.append({"role": "assistant", "content": response_text})
        except Exception as e:
            log_step(step_num, "llm_error", 0.0, False, str(e))
            rewards.append(0.0)
            continue

        try:
            action_dict = parse_llm_action(response_text)
        except (json.JSONDecodeError, ValueError) as e:
            log_step(step_num, "parse_error", 0.0, False, f"JSON parse error: {e}")
            rewards.append(0.0)
            messages.append({
                "role": "user",
                "content": "Error: Your response was not valid JSON. "
                "Please respond with ONLY a JSON action object like: "
                '{"action_type": "add_ingredient", "ingredient": "water", "vessel": "saucepan"}',
            })
            continue

        try:
            action = RasoiAction(**action_dict)
            obs = env.step(action)
            obs_dict = obs_to_dict(obs)

            reward = float(obs.reward or 0.0)
            done = obs.done
            score = float(obs.score)
            rewards.append(reward)
            action_str = action_dict.get("action_type", "unknown")
            log_step(step_num, action_str, reward, done, None)
        except Exception as e:
            log_step(step_num, action_dict.get("action_type", "unknown"), 0.0, False, str(e))
            rewards.append(0.0)

    success = score > 0.1
    log_end(success=success, steps=step_num, score=score, rewards=rewards)
    return score


def main():
    if not API_KEY:
        print("Error: HF_TOKEN or API_KEY environment variable required.", file=sys.stderr)
        sys.exit(1)

    client = OpenAI(base_url=API_BASE_URL, api_key=API_KEY)

    total_score = 0.0
    for task_id in TASKS:
        try:
            score = run_task(client, task_id)
            total_score += score
        except Exception as e:
            print(f"Error running {task_id}: {e}", file=sys.stderr)
            log_end(success=False, steps=0, score=0.0, rewards=[])

    avg_score = total_score / len(TASKS)
    print(f"\nAverage score across all tasks: {avg_score:.2f}", file=sys.stderr)


if __name__ == "__main__":
    main()
