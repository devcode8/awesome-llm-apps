"""Chat API - Main entry point for the tutor agent system."""

from logging import Logger

from tutor_agent.context import TutorContext
from tutor_agent.orchestrator import orchestrator_agent


async def chat(
    session_id: str,
    user_id: str,
    message: str,
    logger: Logger
) -> str:
    logger.info(f"[{session_id}] Received message from user {user_id}: {message}")
    context = TutorContext(user_id=user_id, session_id=session_id)
    config = {"configurable": {"thread_id": session_id}}

    final_response = ""

    async for stream_mode, chunk in orchestrator_agent.astream(
        {"messages": [{"role": "user", "content": message}]},
        config=config,
        stream_mode=["updates", "custom"],
        context=context,
    ):
        if stream_mode == "custom":
            # Custom progress updates emitted by tools via get_stream_writer()
            progress_msg = str(chunk)
            logger.info(f"[{session_id}] Progress: {progress_msg}")

        elif stream_mode == "updates":
            # State updates after each agent step
            for step_name, data in chunk.items():
                if step_name == "__interrupt__":
                    continue

                if not isinstance(data, dict) or "messages" not in data:
                    continue

                for msg in data["messages"]:
                    # Log tool calls for progress visibility
                    tool_calls = getattr(msg, "tool_calls", None)
                    if tool_calls:
                        tool_names = [tc.get("name", "unknown") for tc in tool_calls]
                        logger.info(f"[{session_id}] Tool calls: {tool_names}")

                    # Extract text content — keep updating so the last
                    # non-empty AI message wins as the final response.
                    content = getattr(msg, "content", "")
                    text = _extract_text(content)
                    if text:
                        # Skip tool-result messages; we want the AI's own words
                        msg_type = getattr(msg, "type", "")
                        if msg_type != "tool":
                            final_response = text

    if not final_response:
        # Last-resort: pull from the orchestrator's full state
        try:
            state = orchestrator_agent.get_state(config)
            for msg in reversed(state.values.get("messages", [])):
                if getattr(msg, "type", "") == "ai":
                    text = _extract_text(getattr(msg, "content", ""))
                    if text:
                        final_response = text
                        break
        except Exception:
            pass

    if not final_response:
        final_response = (
            "I'm here to help! Tell me what you'd like to learn or "
            "which exam you're preparing for, and we'll get started right away."
        )

    logger.info(f"[{session_id}] Response generated for user {user_id}")
    return final_response


def _extract_text(content: object) -> str:
    """Pull plain text from various content shapes returned by LangChain."""
    if isinstance(content, str) and content.strip():
        return content.strip()
    if isinstance(content, list):
        parts = [
            block.get("text", "") if isinstance(block, dict) else str(block)
            for block in content
        ]
        joined = "".join(parts).strip()
        if joined:
            return joined
    return ""
