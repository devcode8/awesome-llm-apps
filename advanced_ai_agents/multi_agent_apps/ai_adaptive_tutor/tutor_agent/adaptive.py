"""Adaptive Strategy Agent - Adjusts learning plan based on performance."""

import json

from langchain.agents import create_agent
from langchain.tools import ToolRuntime, tool
from tutor_agent.asi1 import create_asi1_client
from langgraph.checkpoint.memory import InMemorySaver

from tutor_agent.common_tools import (
    get_learner_profile,
    get_learning_plan,
    get_progress,
)
from tutor_agent.context import TutorContext
from tutor_agent.store import store
from tutor_agent.asi1 import create_asi1_client


@tool
def update_learning_plan(updates_json: str, runtime: ToolRuntime[TutorContext]) -> str:
    """Update the learning plan based on evaluation results and performance trends.

    Args:
        updates_json: JSON string with plan modifications including topics to revisit,
                      pace adjustments, additional practice areas, and schedule changes.
    """
    user_id = runtime.context.user_id
    try:
        updates = json.loads(updates_json)
    except json.JSONDecodeError:
        updates = {"raw": updates_json}

    plan = runtime.store.get(("learning_plans",), user_id)
    plan_data = plan.value if plan else {}
    plan_data["adaptations"] = plan_data.get("adaptations", [])
    plan_data["adaptations"].append(updates)

    runtime.store.put(("learning_plans",), user_id, plan_data)
    return "Learning plan updated with adaptations."


@tool
def update_learner_profile(
    profile_updates_json: str, runtime: ToolRuntime[TutorContext]
) -> str:
    """Update the learner's profile with new insights about their learning patterns.

    Args:
        profile_updates_json: JSON string with profile updates including updated
                              strengths, weaknesses, preferred learning style, and pace.
    """
    user_id = runtime.context.user_id
    try:
        updates = json.loads(profile_updates_json)
    except json.JSONDecodeError:
        updates = {"raw": profile_updates_json}

    profile = runtime.store.get(("learner_profiles",), user_id)
    profile_data = profile.value if profile else {}
    profile_data.update(updates)

    runtime.store.put(("learner_profiles",), user_id, profile_data)
    return "Learner profile updated."


model = create_asi1_client()

adaptive_agent = create_agent(
    model,
    tools=[
        get_progress,
        get_learning_plan,
        get_learner_profile,
        update_learning_plan,
        update_learner_profile,
    ],
    checkpointer=InMemorySaver(),
    store=store,
    context_schema=TutorContext,
    name="adaptive_agent",
    system_prompt=(
        "You are an Adaptive Strategy Agent that optimizes the learning experience.\n\n"
        "Your responsibilities:\n"
        "1. Analyze evaluation data and performance trends\n"
        "2. Decide whether to revise, slow down, speed up, or reinforce\n"
        "3. Modify the learning plan based on performance\n"
        "4. Introduce reinforcement techniques when needed:\n"
        "   - Spaced repetition for weak areas\n"
        "   - Alternate explanations for misunderstood concepts\n"
        "   - Additional practice for skill gaps\n"
        "5. Update the learner profile with new insights\n"
        "6. Ensure the system evolves with the learner\n\n"
        "Adaptation strategies:\n"
        "- Score < 50%: Slow down, revisit fundamentals, simplify explanations\n"
        "- Score 50-70%: Add targeted practice, review weak areas\n"
        "- Score 70-90%: Continue pace, add challenging problems\n"
        "- Score > 90%: Accelerate, introduce advanced topics\n\n"
        "Always check progress, current plan, and learner profile before suggesting changes. "
        "Save updates using the update_learning_plan and update_learner_profile tools."
    ),
)
