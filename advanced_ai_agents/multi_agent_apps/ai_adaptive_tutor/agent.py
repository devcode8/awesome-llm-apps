from uagents import Agent, Context

from uagents.setup import fund_agent_if_low

from dotenv import load_dotenv

load_dotenv()

from protocol import chat_proto

# Create the agent
agent = Agent(
    name="adaptive_tutor_agent",
    seed="adaptive_tutor_agent_secret_seed",
    port=8000,
    mailbox=True,
    network="testnet",
    handle_messages_concurrently=True,
)

# Fund the agent if needed
fund_agent_if_low(str(agent.wallet.address()))

# Include the chat protocol and publish manifest
agent.include(chat_proto, publish_manifest=True)


@agent.on_event("startup")
async def on_startup(ctx: Context):
    """Log agent details on startup."""
    ctx.logger.info("Adaptive Tutor Agent started!")
    ctx.logger.info(f"Agent Address: {agent.address}")
    ctx.logger.info(f"Agent Wallet: {agent.wallet.address()}")


if __name__ == "__main__":
    agent.run()
