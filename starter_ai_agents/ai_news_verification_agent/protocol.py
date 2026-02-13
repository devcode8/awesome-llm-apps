import asyncio
import os

from dotenv import load_dotenv
from openai import OpenAI
from uagents import Context, Protocol
from uagents_core.contrib.protocols.chat import (
    ChatAcknowledgement,
    ChatMessage,
    EndSessionContent,
    StartSessionContent,
    TextContent,
    chat_protocol_spec,
)

load_dotenv()

ASI1_API_KEY = os.getenv("ASI1_API_KEY")
asi1_client = OpenAI(
    api_key=ASI1_API_KEY,
    base_url="https://api.asi1.ai/v1"
)

SYSTEM_PROMPT = (
    "You are a news fact-checker. Given a news headline or claim, "
    "use web search results to determine if it is likely real or likely fake. "
    "Respond in this exact format:\n\n"
    "Verdict: [Likely Real / Likely Fake]\n"
    "Explanation: [1-2 sentences explaining why, citing sources if available]"
)


def verify_news(claim: str) -> str:
    """Call ASI1 API with web search enabled to fact-check a news claim."""
    try:
        response = asi1_client.chat.completions.create(
            model="asi1",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": claim},
            ],
            temperature=0.2,
            top_p=0.9,
            max_tokens=1000,
            presence_penalty=0,
            frequency_penalty=0,
            stream=False,
            extra_body={"web_search": True},
        )
        return response.choices[0].message.content or ""
    except Exception as exc:
        return f"Verification failed: {exc}"


chat_protocol = Protocol(spec=chat_protocol_spec)


@chat_protocol.on_message(model=ChatMessage)
async def handle_message(ctx: Context, sender: str, msg: ChatMessage):
    """Handle incoming chat messages."""
    ctx.logger.info(f"Received message from {sender}")

    # ACK the incoming message
    ack = ChatAcknowledgement(acknowledged_msg_id=msg.msg_id)
    await ctx.send(sender, ack)

    for item in msg.content:
        if isinstance(item, StartSessionContent):
            ctx.logger.info(f"Session started with {sender}")
        elif isinstance(item, EndSessionContent):
            ctx.logger.info(f"Session ended with {sender}")
        elif isinstance(item, TextContent):
            claim = item.text
            ctx.logger.info(f"Fact-checking claim: {claim}")

            # Run the synchronous API call in a thread
            verdict = await asyncio.to_thread(verify_news, claim)

            ctx.logger.info(f"Verdict: {verdict}")

            response = ChatMessage(content=[TextContent(text=verdict)])
            await ctx.send(sender, response)


@chat_protocol.on_message(model=ChatAcknowledgement)
async def handle_acknowledgement(ctx: Context, sender: str, msg: ChatAcknowledgement):
    ctx.logger.info(f"Message {msg.acknowledged_msg_id} acknowledged by {sender}")
