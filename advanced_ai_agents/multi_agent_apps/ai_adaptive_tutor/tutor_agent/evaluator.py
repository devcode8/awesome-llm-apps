"""Evaluation Agent - Reviews answers, scores performance, and provides feedback."""

import json

from langchain.agents import create_agent
from tutor_agent.asi1 import create_asi1_client
from langchain.tools import tool, ToolRuntime
from langgraph.checkpoint.memory import InMemorySaver

from tutor_agent.context import TutorContext
from tutor_agent.store import store
from tutor_agent.common_tools import get_progress



@tool
def get_quiz_data(runtime: ToolRuntime[TutorContext]) -> str:
    """Retrieve the current quiz data including questions and expected answers."""
    user_id = runtime.context.user_id
    quiz = runtime.store.get(("current_quiz",), user_id)
    if quiz:
        return json.dumps(quiz.value)
    return "No quiz data found."


@tool
def save_evaluation(evaluation_json: str, runtime: ToolRuntime[TutorContext]) -> str:
    """Save the evaluation results including scores, feedback, and identified gaps.

    Args:
        evaluation_json: JSON string with evaluation data including score,
                         per-question feedback, misconceptions found, and
                         improvement suggestions.
    """
    user_id = runtime.context.user_id
    try:
        eval_data = json.loads(evaluation_json)
    except json.JSONDecodeError:
        eval_data = {"raw": evaluation_json}

    # Update progress with evaluation
    progress = runtime.store.get(("progress",), user_id)
    progress_data = progress.value if progress else {
        "covered_topics": [],
        "quiz_scores": [],
        "evaluations": [],
        "weak_areas": [],
    }

    progress_data["evaluations"].append(eval_data)
    if "score" in eval_data:
        progress_data["quiz_scores"].append(eval_data["score"])
    if "weak_areas" in eval_data:
        for area in eval_data["weak_areas"]:
            if area not in progress_data["weak_areas"]:
                progress_data["weak_areas"].append(area)

    runtime.store.put(("progress",), user_id, progress_data)
    return "Evaluation saved successfully."


model = create_asi1_client()


evaluator_agent = create_agent(
    model,
    tools=[get_progress, get_quiz_data, save_evaluation],
    checkpointer=InMemorySaver(),
    store=store,
    context_schema=TutorContext,
    name="evaluator_agent",
    system_prompt=(
        "You are an Evaluation Agent that reviews learner answers and provides feedback.\n\n"
        "Your responsibilities:\n"
        "1. Compare user answers against expected answers from the quiz\n"
        "2. Score performance (percentage correct)\n"
        "3. Identify misconceptions and conceptual gaps\n"
        "4. Provide constructive, encouraging feedback for each question\n"
        "5. Explain why answers are correct or incorrect\n"
        "6. Suggest specific improvement strategies\n"
        "7. Track performance trends over time\n\n"
        "Feedback guidelines:\n"
        "- Be specific about what was right and what needs improvement\n"
        "- Relate feedback to underlying concepts\n"
        "- Suggest targeted review for weak areas\n"
        "- Celebrate progress and correct answers\n\n"
        "Always get the quiz data first, then evaluate the learner's answers, "
        "and finally save the evaluation results using the save_evaluation tool."
    ),
)
