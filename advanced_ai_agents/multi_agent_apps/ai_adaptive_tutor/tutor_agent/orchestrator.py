"""Orchestrator Agent - Main coordinator that manages the learning workflow."""

import json

from langchain.agents import create_agent
from langchain.tools import tool, ToolRuntime
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.config import get_stream_writer

from tutor_agent.asi1 import create_asi1_client
from tutor_agent.context import TutorContext
from tutor_agent.store import store
from tutor_agent.research import research_agent
from tutor_agent.planner import planner_agent
from tutor_agent.explainer import explainer_agent
from tutor_agent.quiz import quiz_agent
from tutor_agent.evaluator import evaluator_agent
from tutor_agent.adaptive import adaptive_agent


# ---------------------------------------------------------------------------
# Delegation tools — each invokes a sub-agent and streams progress updates
# ---------------------------------------------------------------------------


@tool
def delegate_to_research(message: str, runtime: ToolRuntime[TutorContext]) -> str:
    """Delegate to the Research Agent for topic analysis and syllabus research.
    Use this when the learner specifies a new learning goal, exam, or subject
    and you need to understand the scope of the material.

    Args:
        message: Description of the learning goal or topic to research.
    """
    writer = get_stream_writer()
    writer("Research Agent: Starting topic and syllabus analysis...")

    session_id = runtime.context.session_id
    user_id = runtime.context.user_id

    result = research_agent.invoke(
        {"messages": [{"role": "user", "content": message}]},
        {"configurable": {"thread_id": f"{session_id}_research"}},
        context=TutorContext(user_id=user_id, session_id=session_id),
    )

    writer("Research Agent: Topic analysis complete")
    return str(result["messages"][-1].content)


@tool
def delegate_to_planner(message: str, runtime: ToolRuntime[TutorContext]) -> str:
    """Delegate to the Planner Agent to create or update a learning roadmap.
    Use this after research is complete or when the learner's schedule changes.

    Args:
        message: Instructions for planning including any constraints or preferences.
    """
    writer = get_stream_writer()
    writer("Planner Agent: Creating personalized learning roadmap...")

    session_id = runtime.context.session_id
    user_id = runtime.context.user_id

    result = planner_agent.invoke(
        {"messages": [{"role": "user", "content": message}]},
        {"configurable": {"thread_id": f"{session_id}_planner"}},
        context=TutorContext(user_id=user_id, session_id=session_id),
    )

    writer("Planner Agent: Learning roadmap ready")
    return str(result["messages"][-1].content)


@tool
def delegate_to_explainer(message: str, runtime: ToolRuntime[TutorContext]) -> str:
    """Delegate to the Explainer Agent to teach a concept or topic.
    Use this when it's time to learn a new topic from the plan, or when
    the learner asks a question about a concept.

    Args:
        message: The topic to explain or the learner's question about a concept.
    """
    writer = get_stream_writer()
    writer("Explainer Agent: Preparing lesson...")

    session_id = runtime.context.session_id
    user_id = runtime.context.user_id

    result = explainer_agent.invoke(
        {"messages": [{"role": "user", "content": message}]},
        {"configurable": {"thread_id": f"{session_id}_explainer"}},
        context=TutorContext(user_id=user_id, session_id=session_id),
    )

    writer("Explainer Agent: Lesson delivered")
    return str(result["messages"][-1].content)


@tool
def delegate_to_quiz(message: str, runtime: ToolRuntime[TutorContext]) -> str:
    """Delegate to the Quiz Agent to generate assessment questions.
    Use this after a topic has been explained to test understanding.

    Args:
        message: The topic or module to create quiz questions for.
    """
    writer = get_stream_writer()
    writer("Quiz Agent: Generating assessment questions...")

    session_id = runtime.context.session_id
    user_id = runtime.context.user_id

    result = quiz_agent.invoke(
        {"messages": [{"role": "user", "content": message}]},
        {"configurable": {"thread_id": f"{session_id}_quiz"}},
        context=TutorContext(user_id=user_id, session_id=session_id),
    )

    writer("Quiz Agent: Questions ready")
    return str(result["messages"][-1].content)


@tool
def delegate_to_evaluator(message: str, runtime: ToolRuntime[TutorContext]) -> str:
    """Delegate to the Evaluation Agent to review answers and provide feedback.
    Use this when the learner has answered quiz questions and needs feedback.

    Args:
        message: The learner's answers and any additional context for evaluation.
    """
    writer = get_stream_writer()
    writer("Evaluation Agent: Reviewing answers...")

    session_id = runtime.context.session_id
    user_id = runtime.context.user_id

    result = evaluator_agent.invoke(
        {"messages": [{"role": "user", "content": message}]},
        {"configurable": {"thread_id": f"{session_id}_evaluator"}},
        context=TutorContext(user_id=user_id, session_id=session_id),
    )

    writer("Evaluation Agent: Review complete")
    return str(result["messages"][-1].content)


@tool
def delegate_to_adaptive(message: str, runtime: ToolRuntime[TutorContext]) -> str:
    """Delegate to the Adaptive Strategy Agent to adjust the learning plan.
    Use this after evaluation to optimize the learning experience based on
    the learner's performance trends.

    Args:
        message: Evaluation summary and context for strategy adaptation.
    """
    writer = get_stream_writer()
    writer("Adaptive Strategy Agent: Optimizing learning strategy...")

    session_id = runtime.context.session_id
    user_id = runtime.context.user_id

    result = adaptive_agent.invoke(
        {"messages": [{"role": "user", "content": message}]},
        {"configurable": {"thread_id": f"{session_id}_adaptive"}},
        context=TutorContext(user_id=user_id, session_id=session_id),
    )

    writer("Adaptive Strategy Agent: Strategy updated")
    return str(result["messages"][-1].content)


# ---------------------------------------------------------------------------
# Learner profile & progress tools — direct store access
# ---------------------------------------------------------------------------


@tool
def get_learner_profile(runtime: ToolRuntime[TutorContext]) -> str:
    """Retrieve the learner's profile to understand their current state,
    goals, preferences, strengths, and weaknesses."""
    user_id = runtime.context.user_id
    profile = runtime.store.get(("learner_profiles",), user_id)
    if profile:
        return json.dumps(profile.value)
    return "No learner profile found. Need to gather learner information."


@tool
def save_learner_profile(profile_json: str, runtime: ToolRuntime[TutorContext]) -> str:
    """Save or update the learner's profile with their goals, level,
    preferences, and constraints.

    Args:
        profile_json: JSON string with learner profile data including goal,
                      current_level, available_time, learning_preferences,
                      and any other relevant information.
    """
    writer = get_stream_writer()
    user_id = runtime.context.user_id
    try:
        data = json.loads(profile_json)
    except json.JSONDecodeError:
        data = {"raw": profile_json}

    existing = runtime.store.get(("learner_profiles",), user_id)
    if existing:
        profile_data = existing.value
        profile_data.update(data)
    else:
        profile_data = data

    runtime.store.put(("learner_profiles",), user_id, profile_data)
    writer("Learner profile saved")
    return "Learner profile saved successfully."


@tool
def get_session_progress(runtime: ToolRuntime[TutorContext]) -> str:
    """Get a comprehensive overview of the learner's journey including
    their profile, progress, and current learning plan status."""
    user_id = runtime.context.user_id

    progress = runtime.store.get(("progress",), user_id)
    plan = runtime.store.get(("learning_plans",), user_id)
    profile = runtime.store.get(("learner_profiles",), user_id)

    overview = {
        "profile": profile.value if profile else None,
        "progress": progress.value if progress else None,
        "plan": plan.value if plan else None,
    }

    return json.dumps(overview)


# ---------------------------------------------------------------------------
# Orchestrator agent
# ---------------------------------------------------------------------------

model = create_asi1_client()

orchestrator_agent = create_agent(
    model,
    tools=[
        delegate_to_research,
        delegate_to_planner,
        delegate_to_explainer,
        delegate_to_quiz,
        delegate_to_evaluator,
        delegate_to_adaptive,
        get_learner_profile,
        save_learner_profile,
        get_session_progress,
    ],
    checkpointer=InMemorySaver(),
    store=store,
    context_schema=TutorContext,
    name="orchestrator",
    system_prompt=(
        "You are a friendly, action-oriented personal tutor.\n\n"
        "CORE PRINCIPLE: ACT FAST, ASK LITTLE.\n"
        "- Infer the subject, level, and needs from context. Do NOT ask lengthy questionnaires.\n"
        "- If the learner says 'fraction multiplication exam tomorrow', you already know: "
        "subject=mathematics, topic=fraction multiplication, urgency=high, style=quick review.\n"
        "- Ask at most ONE short clarifying question if truly necessary, then START HELPING.\n"
        "- Default to action: save what you know, research the topic, and begin teaching.\n\n"
        "AVAILABLE AGENTS (use via delegation tools):\n"
        "1. Research Agent (delegate_to_research) - Analyzes topics and builds topic maps\n"
        "2. Planner Agent (delegate_to_planner) - Creates learning roadmaps\n"
        "3. Explainer Agent (delegate_to_explainer) - Teaches concepts step by step\n"
        "4. Quiz Agent (delegate_to_quiz) - Generates assessment questions\n"
        "5. Evaluation Agent (delegate_to_evaluator) - Reviews answers and scores\n"
        "6. Adaptive Strategy Agent (delegate_to_adaptive) - Adjusts plan based on performance\n\n"
        "WORKFLOW:\n"
        "1. Extract whatever info you can from the learner's message (goal, subject, level, "
        "time, preferences). Save it with save_learner_profile immediately.\n"
        "2. Delegate to Research Agent for the topic.\n"
        "3. Delegate to Planner Agent for a roadmap.\n"
        "4. Start the learning cycle: Explain -> Quiz -> Evaluate -> Adapt -> Next topic.\n\n"
        "WHEN THE LEARNER IS IN A HURRY:\n"
        "- Skip lengthy research; go straight to Explainer for a quick review.\n"
        "- Follow up with a fast Quiz to test readiness.\n"
        "- Keep everything concise and focused.\n\n"
        "FOR ONGOING SESSIONS:\n"
        "- Check progress with get_session_progress to resume where they left off.\n\n"
        "GUIDELINES:\n"
        "- Always present sub-agent responses directly to the learner (they are the reply).\n"
        "- Never expose internal agent names or technical details.\n"
        "- Be encouraging, structured, and goal-driven.\n"
        "- When the learner asks a concept question, delegate to Explainer immediately.\n"
        "- When the learner wants testing, delegate to Quiz immediately.\n"
        "- When the learner provides quiz answers, delegate to Evaluator immediately."
    ),

)
