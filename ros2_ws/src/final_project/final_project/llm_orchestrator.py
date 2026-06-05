#
# MOBILE ROBOTS - FI-UNAM, 2026-2
# FINAL PROJECT - LLM TASK PLANNER (Ollama / llama3)
#
# Turns a free-form spoken command into an ordered list of robot
# sub-tasks (a "plan"), using a locally running llama3 model served
# by Ollama. The output is constrained to a JSON schema so it is
# always parseable. No cloud APIs are used.
#
# This module is pure Python (no rclpy) so it can be unit-tested
# without a running ROS graph.
#
import json
import requests

OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL = "llama3"

# The only verbs the robot knows how to execute. The orchestrator state
# machine (sm_orchestrator.py) maps each one to a ROS action.
ALLOWED_ACTIONS = ["move_to", "find", "grasp", "place", "say", "return_to_user"]

# JSON schema sent to Ollama via the "format" field. Ollama >= 0.5 uses it
# to constrain decoding, so the model is forced to emit valid, parseable JSON.
PLAN_SCHEMA = {
    "type": "object",
    "properties": {
        "steps": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "action": {"type": "string", "enum": ALLOWED_ACTIONS},
                    "target": {"type": "string"},
                    "text":   {"type": "string"},
                },
                "required": ["action"],
            },
        }
    },
    "required": ["steps"],
}

# Known symbolic locations -> map coordinates [x, y, yaw] (meters, rad).
# Adjust these to match your apartment map (motion_planning/maps/appartment.yaml).
KNOWN_LOCATIONS = {
    "living_room": [3.0, 1.5, 0.0],
    "kitchen":     [1.0, 4.0, 1.57],
    "bedroom":     [-2.0, 2.0, 3.14],
    "user":        [0.0, 0.0, 0.0],   # where the command was issued
}

SYSTEM_PROMPT = (
    "You are the task planner of a domestic mobile robot with a camera and an arm. "
    "Decompose the user's command into an ordered list of steps. "
    "Use ONLY these actions: move_to(target=location), find(target=object), "
    "grasp(target=object), place(target=location), return_to_user(), say(text=...). "
    f"Valid locations are: {', '.join(KNOWN_LOCATIONS.keys())}. "
    "A typical fetch command expands to: move_to a room, find the object, grasp it, "
    "return_to_user, say a short confirmation. "
    "Answer ONLY with JSON matching the schema. Keep 'say' texts under 12 words."
)

# One in-context example improves small-model reliability a lot.
FEWSHOT_USER = "Tr\u00e1eme el control remoto de la sala"
FEWSHOT_ASSISTANT = json.dumps({
    "steps": [
        {"action": "move_to", "target": "living_room"},
        {"action": "find", "target": "remote"},
        {"action": "grasp", "target": "remote"},
        {"action": "return_to_user"},
        {"action": "say", "text": "Aqu\u00ed tienes el control."},
    ]
}, ensure_ascii=False)


def plan_from_command(command, timeout=60.0):
    """Send the command to llama3 and return a list of step dicts.

    Raises RuntimeError if the model is unreachable or returns invalid data.
    """
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": FEWSHOT_USER},
        {"role": "assistant", "content": FEWSHOT_ASSISTANT},
        {"role": "user", "content": command},
    ]
    payload = {
        "model": MODEL,
        "messages": messages,
        "format": PLAN_SCHEMA,       # schema-constrained output
        "stream": False,
        "options": {"temperature": 0, "num_ctx": 8192},
    }
    try:
        resp = requests.post(OLLAMA_URL, json=payload, timeout=timeout)
        resp.raise_for_status()
    except requests.RequestException as e:
        raise RuntimeError(f"Ollama request failed: {e}")

    content = resp.json()["message"]["content"]
    try:
        data = json.loads(content)
    except json.JSONDecodeError as e:
        raise RuntimeError(f"LLM did not return valid JSON: {e}\n{content}")

    steps = data.get("steps", [])
    clean = []
    for s in steps:
        action = s.get("action")
        if action not in ALLOWED_ACTIONS:
            continue                 # drop hallucinated verbs
        clean.append({
            "action": action,
            "target": s.get("target"),
            "text": s.get("text"),
        })
    if not clean:
        raise RuntimeError(f"Empty/invalid plan: {content}")
    return clean


if __name__ == "__main__":
    # Quick manual test:  python3 llm_orchestrator.py "Get me the TV remote"
    import sys
    cmd = " ".join(sys.argv[1:]) or "Get me the TV remote controller"
    for i, step in enumerate(plan_from_command(cmd), 1):
        print(f"{i:2d}. {step}")