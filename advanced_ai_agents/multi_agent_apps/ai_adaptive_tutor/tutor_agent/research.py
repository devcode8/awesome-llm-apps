"""Research Agent - Analyzes learning goals, topics, and syllabus structure."""

import json

from langchain.agents import create_agent
from tutor_agent.asi1 import create_asi1_client
from langchain.tools import tool, ToolRuntime
from langgraph.checkpoint.memory import InMemorySaver

from tutor_agent.context import TutorContext
from tutor_agent.store import store


@tool
def search_web(query: str) -> str:
    """Search the web for syllabus structure, important topics,
    common question types, and difficulty levels for a given subject or exam.

    Args:
        query: Search query about a subject, exam, or learning topic.
    """
    # Simulated web search - in production, integrate an actual search API
    return (
        f"Search results for '{query}':\n"
        "Found comprehensive information including:\n"
        "- Core fundamentals and prerequisites\n"
        "- Key concepts organized by difficulty (beginner -> intermediate -> advanced)\n"
        "- Common exam question patterns and frequently tested topics\n"
        "- Topic dependencies (what needs to be learned before what)\n"
        "- Estimated study time for each topic area\n"
        "- High-impact topics that appear most frequently in assessments\n\n"
        "Please synthesize this information into a structured topic map."
    )


@tool
def save_topic_map(topic_map_json: str, runtime: ToolRuntime[TutorContext]) -> str:
    """Save the structured topic map to long-term memory for use by the planner.

    Args:
        topic_map_json: JSON string with the topic map containing topics, subtopics,
                        difficulty levels, dependencies, importance rankings, and
                        estimated time per topic.
    """
    user_id = runtime.context.user_id
    try:
        data = json.loads(topic_map_json)
    except json.JSONDecodeError:
        data = {"raw": topic_map_json}
    runtime.store.put(("topic_maps",), user_id, data)
    return "Topic map saved successfully."


model = create_asi1_client()


research_agent = create_agent(
    model,
    tools=[search_web, save_topic_map],
    checkpointer=InMemorySaver(),
    store=store,
    context_schema=TutorContext,
    name="research_agent",
    system_prompt=(
        "You are a Research Agent specialized in understanding the scope of learning goals.\n\n"
        "Your responsibilities:\n"
        "1. When given a learning topic, exam, or subject, search for comprehensive information\n"
        "2. Identify all key topics, subtopics, and their dependencies\n"
        "3. Rank topics by importance (high/medium/low) and difficulty (beginner/intermediate/advanced)\n"
        "4. Identify common question types and exam patterns\n"
        "5. Estimate time needed for each topic\n"
        "6. Prioritize high-impact topics that frequently appear in assessments\n\n"
        "Output a structured topic map as JSON with the following format:\n"
        '{"subject": "...", "topics": [{"name": "...", "subtopics": [...], '
        '"difficulty": "beginner|intermediate|advanced", "importance": "high|medium|low", '
        '"estimated_hours": N, "prerequisites": [...]}]}\n\n'
        "Always save the topic map using the save_topic_map tool before finishing."
    ),
)
