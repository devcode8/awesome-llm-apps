"""Planner Agent - Creates realistic, personalized learning roadmaps."""

import json

from langchain.agents import create_agent
from tutor_agent.asi1 import create_asi1_client
from langchain.tools import tool, ToolRuntime
from langgraph.checkpoint.memory import InMemorySaver

from tutor_agent.context import TutorContext
from tutor_agent.store import store
from tutor_agent.common_tools import get_topic_map, get_learner_profile


@tool
def save_learning_plan(plan_json: str, runtime: ToolRuntime[TutorContext]) -> str:
    """Save the learning plan/roadmap to long-term memory.

    Args:
        plan_json: JSON string with the learning plan containing modules,
                   scheduled topics, revision cycles, checkpoints, and deadlines.
    """
    user_id = runtime.context.user_id
    try:
        data = json.loads(plan_json)
    except json.JSONDecodeError:
        data = {"raw": plan_json}
    runtime.store.put(("learning_plans",), user_id, data)
    return "Learning plan saved successfully."


model = create_asi1_client()


planner_agent = create_agent(
    model,
    tools=[get_topic_map, get_learner_profile, save_learning_plan],
    checkpointer=InMemorySaver(),
    store=store,
    context_schema=TutorContext,
    name="planner_agent",
    system_prompt=(
        "You are a Planner Agent that creates realistic, personalized learning roadmaps.\n\n"
        "Your responsibilities:\n"
        "1. Read the topic map from research and the learner's profile\n"
        "2. Consider available time, learning pace, deadlines, and cognitive load\n"
        "3. Create a structured module-based learning plan\n"
        "4. Include revision cycles and spaced repetition\n"
        "5. Add checkpoints for progress assessment\n"
        "6. Ensure the plan is achievable, not overwhelming\n"
        "7. Adapt if the user falls behind or progresses faster\n\n"
        "Output the plan as JSON:\n"
        '{"total_duration": "...", "modules": [{"module_number": N, "title": "...", '
        '"topics": [...], "duration": "...", "activities": ["learn", "practice", "quiz"], '
        '"revision_of": [...]}]}\n\n'
        "Always start by reading the topic map and learner profile, then create and save the plan."
    ),
)
