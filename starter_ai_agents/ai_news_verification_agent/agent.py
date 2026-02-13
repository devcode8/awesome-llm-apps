from uagents import Agent, Context
from uagents.setup import fund_agent_if_low

from protocols import chat_protocol

# --- Agent setup ---
agent = Agent(
    name="news_verification_agent",
    seed="news-verify-secret",
    port=8001,
    mailbox=True
)

fund_agent_if_low(str(agent.wallet.address()))

@agent.on_event("startup")
async def on_startup(ctx: Context):
    """Log agent details on startup."""
    ctx.logger.info("News Verification Agent started!")
    ctx.logger.info(f"Agent Address: {agent.address}")
    ctx.logger.info(f"Agent Wallet: {agent.wallet.address()}")


agent.include(chat_protocol, publish_manifest=True)

if __name__ == "__main__":
    agent.run()
