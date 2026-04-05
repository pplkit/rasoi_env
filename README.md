---
title: Rasoi - Indian Cooking Assistant
emoji: 🍳
colorFrom: yellow
colorTo: red
sdk: docker
app_port: 8000
base_path: /web
tags:
  - openenv
---

# Rasoi - Indian Cooking Assistant

A virtual Indian kitchen RL environment where an AI agent learns to cook authentic recipes by following instructions, managing timing across multiple vessels, and handling dietary constraints.

## Quick Start

```python
from rasoi_env import RasoiEnv, RasoiAction

with RasoiEnv(base_url="http://localhost:8000") as client:
    result = client.reset()
    result = client.step(RasoiAction(
        action_type="add_ingredient",
        ingredient="water",
        vessel="saucepan"
    ))
```

## Tasks

| Task | Difficulty | Dish | Description |
|------|-----------|------|-------------|
| `task_1` | Easy | Masala Chai | Follow a 5-step recipe to make Indian spiced tea. |
| `task_2` | Medium | Dairy-Free Pancakes | Make pancakes with dairy-free substitutions. |
| `task_3` | Hard | Indian Thali | Cook 3 dishes simultaneously (Dal, Rice, Aloo Gobi). |

## Action Space

| Action | Required Params | Description |
|--------|----------------|-------------|
| `add_ingredient` | ingredient, vessel | Add ingredient from pantry |
| `set_heat` | vessel, heat_level | Set heat: off/low/medium/high |
| `cook` | vessel, duration_minutes | Cook for N minutes (global time advance) |
| `stir` | vessel | Stir vessel contents |
| `chop` | ingredient, chop_style | Chop: dice/mince/slice/julienne |
| `mix` | vessel | Mix/combine contents |
| `transfer` | from_vessel, to_vessel | Move contents between vessels |
| `serve` | vessel, dish_name | Serve completed dish |
| `check_status` | vessel | Inspect vessel (no time) |
| `wait` | duration_minutes | Wait (global time advance) |

## Observation Space

- `vessels`: State of all cooking vessels
- `available_ingredients`: Pantry inventory
- `recipe`: Recipe instructions
- `current_time`: Elapsed minutes
- `dietary_constraints`: Active restrictions
- `feedback`: Result of last action
- `completed_dishes`: Dishes served
- `score`, `done`, `reward`

## Reward Design

Per-step: +0.1 correct step, +0.2 correct substitution, -0.05 wrong ingredient, -0.1 burned food, +0.3 dish served.
Episode scores normalized to 0.0-1.0.

## Setup

```bash
cd rasoi_env
uv sync
uv run server
```

## Docker

```bash
docker build -t rasoi_env -f server/Dockerfile .
docker run -p 8000:8000 rasoi_env
```

## Inference

```bash
export API_BASE_URL="https://router.huggingface.co/v1"
export MODEL_NAME="Qwen/Qwen2.5-72B-Instruct"
export HF_TOKEN="your-token"
python inference.py
```

## Baseline Scores

| Task | Score |
|------|-------|
| task_1 (Masala Chai) | TBD |
| task_2 (Dairy-Free Pancakes) | TBD |
| task_3 (Indian Thali) | TBD |
