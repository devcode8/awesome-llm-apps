"""Explainer Agent - Teaching component that presents concepts clearly."""

from langchain.agents import create_agent
from langchain.tools import ToolRuntime, tool
from tutor_agent.asi1 import create_asi1_client
from langgraph.checkpoint.memory import InMemorySaver

from tutor_agent.common_tools import get_learning_plan, get_progress
from tutor_agent.context import TutorContext
from tutor_agent.store import store


@tool
def mark_topic_covered(topic_name: str, notes: str, runtime: ToolRuntime[TutorContext]) -> str:
    """Mark a topic as covered and save teaching notes to progress tracking.

    Args:
        topic_name: The name of the topic that was just taught.
        notes: Brief notes about what was covered and any areas the learner struggled with.
    """
    user_id = runtime.context.user_id
    progress = runtime.store.get(("progress",), user_id)
    progress_data = progress.value if progress else {
        "covered_topics": [],
        "quiz_scores": [],
        "evaluations": [],
        "weak_areas": [],
    }

    progress_data["covered_topics"].append({
        "topic": topic_name,
        "notes": notes,
    })

    runtime.store.put(("progress",), user_id, progress_data)
    return f"Topic '{topic_name}' marked as covered."


model = create_asi1_client()


explainer_agent = create_agent(
    model,
    tools=[get_learning_plan, get_progress, mark_topic_covered],
    checkpointer=InMemorySaver(),
    store=store,
    context_schema=TutorContext,
    name="explainer_agent",
    system_prompt=(
        "You are an Explainer Agent - the teaching component of a personal tutor system.\n\n"
        "Your responsibilities:\n"
        "1. Present concepts clearly, starting from fundamentals\n"
        "2. Gradually increase complexity as understanding develops\n"
        "3. Use examples, analogies, visual descriptions, and real-world applications\n"
        "4. Be interactive - encourage the learner to think rather than passively read\n"
        "5. Adjust explanation depth based on learner understanding and feedback\n"
        "6. Mark topics as covered when done teaching them\n\n"
        "Teaching style:\n"
        "- Start with 'why' before 'what' and 'how'\n"
        "- Use step-by-step breakdowns for complex topics\n"
        "- Include inline thought questions to engage the learner\n"
        "- Relate new concepts to previously learned material\n"
        "- Use markdown formatting for clear structure\n\n"
        "Check the learning plan for the current topic if applicable, "
        "and check progress to avoid re-teaching covered material."
    ),
)
