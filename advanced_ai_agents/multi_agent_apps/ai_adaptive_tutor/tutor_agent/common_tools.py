"""Shared tool definitions used across multiple sub-agents for store access."""

import json

from langchain.tools import tool, ToolRuntime

from tutor_agent.context import TutorContext


@tool
def get_learner_profile(runtime: ToolRuntime[TutorContext]) -> str:
    """Retrieve the learner's profile including their goal, current level,
    time constraints, learning preferences, strengths, and weaknesses."""
    user_id = runtime.context.user_id
    profile = runtime.store.get(("learner_profiles",), user_id)
    if profile:
        return json.dumps(profile.value)
    return "No learner profile found yet."


@tool
def get_topic_map(runtime: ToolRuntime[TutorContext]) -> str:
    """Retrieve the researched topic map containing subjects, subtopics,
    difficulty levels, dependencies, and importance rankings."""
    user_id = runtime.context.user_id
    topic_map = runtime.store.get(("topic_maps",), user_id)
    if topic_map:
        return json.dumps(topic_map.value)
    return "No topic map found. Research needs to be done first."


@tool
def get_learning_plan(runtime: ToolRuntime[TutorContext]) -> str:
    """Retrieve the current learning plan/roadmap including scheduled topics,
    revision cycles, and checkpoints."""
    user_id = runtime.context.user_id
    plan = runtime.store.get(("learning_plans",), user_id)
    if plan:
        return json.dumps(plan.value)
    return "No learning plan found. A plan needs to be created first."


@tool
def get_progress(runtime: ToolRuntime[TutorContext]) -> str:
    """Retrieve the learner's progress including covered topics, quiz scores,
    evaluation results, and identified weak areas."""
    user_id = runtime.context.user_id
    progress = runtime.store.get(("progress",), user_id)
    if progress:
        return json.dumps(progress.value)
    return "No progress data recorded yet."
