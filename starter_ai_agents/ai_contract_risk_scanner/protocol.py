import traceback
from datetime import datetime, timezone
from uuid import uuid4
from uagents import Context, Protocol
from uagents_core.contrib.protocols.chat import (
    ChatAcknowledgement,
    ChatMessage,
    EndSessionContent,
    TextContent,
    chat_protocol_spec,
)
from asi1 import chat

# Initialize the chat protocol with the standard chat spec
chat_proto = Protocol(spec=chat_protocol_spec)


# ============== Chat Handlers ==============

def create_text_chat(text: str, end_session: bool = False) -> ChatMessage:
    """Wrap plain text into a ChatMessage."""
    content: list = [TextContent(type="text", text=text)]
    if end_session:
        content.append(EndSessionContent(type="end-session"))
    return ChatMessage(
        timestamp=datetime.now(timezone.utc),
        msg_id=uuid4(),
        content=content,
    )

@chat_proto.on_message(ChatMessage)
async def handle_message(ctx: Context, sender: str, msg: ChatMessage):
    """Handle incoming chat messages with session context (RAG)."""
    try:
        ctx.logger.info(f"Received message from {sender}")

        # Send acknowledgement
        await ctx.send(
            sender,
            ChatAcknowledgement(
                timestamp=datetime.now(timezone.utc),
                acknowledged_msg_id=msg.msg_id,
            ),
        )
        
        text_content = ""
        for content in msg.content:
            if isinstance(content, TextContent):
                text_content += content.text
                ctx.logger.info(f"Processing text content from {sender}: {text_content}")
        
        if not text_content.strip():
            ctx.logger.warning(f"No text content found in message from {sender}")
            await ctx.send(
                sender,
                create_text_chat("Sorry, I can only process text messages. Please try again.")
            )
            return
        
        response = await chat(
            session_id=str(ctx.session),
            message=text_content,
        )
        
        if not response.strip():
            ctx.logger.warning(f"Chat function returned empty response for message from {sender}")
            await ctx.send(
                sender,
                create_text_chat("Sorry, I couldn't generate a response. Please try again.")
            )
            return
        await ctx.send(sender, create_text_chat(response))


    except Exception as e:
        ctx.logger.error(f"Error in handle_message: {e}")
        ctx.logger.error(f"Traceback: {traceback.format_exc()}")
        try:
            await ctx.send(
                sender,
                create_text_chat("Sorry, I encountered a technical issue. Please try again.")
            )
        except Exception as send_error:
            ctx.logger.error(f"Failed to send error message: {send_error}")


@chat_proto.on_message(ChatAcknowledgement)
async def handle_acknowledgement(ctx: Context, sender: str, msg: ChatAcknowledgement):
    """Handle acknowledgements for sent messages."""
    ctx.logger.info(
        f"Received acknowledgement from {sender} for message {msg.acknowledged_msg_id}"
    )
