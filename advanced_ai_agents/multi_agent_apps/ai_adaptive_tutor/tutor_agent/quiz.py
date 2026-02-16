"""Quiz Agent - Generates assessment tasks of varying difficulty."""

import json

from langchain.agents import create_agent
from tutor_agent.asi1 import create_asi1_client
from langchain.tools import tool, ToolRuntime
from langgraph.checkpoint.memory import InMemorySaver

from tutor_agent.context import TutorContext
from tutor_agent.store import store
from tutor_agent.common_tools import get_learning_plan, get_progress


@tool
def save_quiz(quiz_json: str, runtime: ToolRuntime[TutorContext]) -> str:
    """Save the generated quiz questions and expected answers to memory.

    Args:
        quiz_json: JSON string with quiz data including questions, options,
                   correct answers, difficulty level, and topic covered.
    """
    user_id = runtime.context.user_id
    try:
        data = json.loads(quiz_json)
    except json.JSONDecodeError:
        data = {"raw": quiz_json}
    runtime.store.put(("current_quiz",), user_id, data)
    return "Quiz saved successfully."


model = create_asi1_client()


quiz_agent = create_agent(
    model,
    tools=[get_learning_plan, get_progress, save_quiz],
    checkpointer=InMemorySaver(),
    store=store,
    context_schema=TutorContext,
    name="quiz_agent",
    system_prompt=(
        "You are a Quiz Agent responsible for generating assessment tasks.\n\n"
        "Your responsibilities:\n"
        "1. Create questions of varying difficulty after each concept or module\n"
        "2. Include multiple question types:\n"
        "   - Multiple choice questions (MCQ)\n"
        "   - Short answer questions\n"
        "   - Problem-solving exercises\n"
        "   - Scenario-based questions\n"
        "   - True/False with explanation\n"
        "3. Increase difficulty when the learner performs well\n"
        "4. Simplify when the learner struggles\n"
        "5. Ensure coverage of key concepts\n\n"
        "Question design principles:\n"
        "- Test understanding, not just memorization\n"
        "- Include distractors that address common misconceptions\n"
        "- Provide clear, unambiguous question text\n"
        "- Cover both conceptual and applied knowledge\n\n"
        "Save the quiz using the save_quiz tool. Present questions to the learner "
        "in a clear, numbered format. Do NOT reveal the correct answers until "
        "the learner has answered."
    ),
)
