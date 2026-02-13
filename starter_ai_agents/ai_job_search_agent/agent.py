from uagents import Agent, Context

from uagents.setup import fund_agent_if_low

from protocol import chat_proto

# Create the agent
agent = Agent(
    name="job_search_agent",
    seed="job_search_agent_secret_",
    port=8000,
    mailbox=True,
)

# Fund the agent if needed
fund_agent_if_low(str(agent.wallet.address()))

# Include the chat protocol and publish manifest
agent.include(chat_proto, publish_manifest=True)


@agent.on_event("startup")
async def on_startup(ctx: Context):
    """Log agent details on startup."""
    ctx.logger.info("Job Search Agent started!")
    ctx.logger.info(f"Agent Address: {agent.address}")
    ctx.logger.info(f"Agent Wallet: {agent.wallet.address()}")


if __name__ == "__main__":
    agent.run()
