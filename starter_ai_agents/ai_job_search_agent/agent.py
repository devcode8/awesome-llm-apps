import asyncio
import re, os
import traceback
from datetime import datetime, timezone
from typing import Dict, Any, List
from uuid import uuid4
from dotenv import load_dotenv
from openai import OpenAI
from uagents import Agent, Context, Protocol
from uagents.setup import fund_agent_if_low
from uagents_core.contrib.protocols.chat import (
    ChatAcknowledgement,
    ChatMessage,
    EndSessionContent,
    StartSessionContent,
    TextContent,
    chat_protocol_spec,
)
load_dotenv()
# ASI1 API Configuration
ASI1_API_KEY = os.getenv("ASI1_API_KEY")
client = OpenAI(
    api_key=ASI1_API_KEY,
    base_url="https://api.asi1.ai/v1"
)

# Create the agent
agent = Agent(
    name="job_search_agent",
    seed="job_search_agent_secret_",
    port=8000,
    mailbox=True,
)

# Fund the agent if needed
fund_agent_if_low(str(agent.wallet.address()))

# Initialize the chat protocol with the standard chat spec
chat_proto = Protocol(spec=chat_protocol_spec)


# ============== Session Storage Functions (RAG Support) ==============

def get_session_key(sender: str, session_id: str) -> str:
    """Generate a unique storage key for a session."""
    return f"session:{sender}:{session_id}"


def get_session_data(ctx: Context, sender: str, session_id: str) -> Dict[str, Any]:
    """Retrieve session data from agent storage."""
    key = get_session_key(sender, session_id)

    if ctx.storage.has(key):
        data = ctx.storage.get(key)
        if isinstance(data, dict):
            ctx.logger.info(f"Loaded session: {session_id}, {len(data.get('history', []))} messages")
            return data

    ctx.logger.info(f"Creating new session: {session_id}")
    return {
        "history": [],
        "state": {
            "greeted": False,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "search_preferences": {},
            "saved_jobs": []
        }
    }


def save_session_data(ctx: Context, sender: str, session_id: str, session_data: Dict[str, Any]) -> None:
    """Save session data to agent storage."""
    key = get_session_key(sender, session_id)
    session_data["state"]["updated_at"] = datetime.now(timezone.utc).isoformat()
    ctx.storage.set(key, session_data)
    ctx.logger.info(f"Saved session: {session_id}, {len(session_data.get('history', []))} messages")


def add_to_history(history: List[Dict], role: str, content: str) -> List[Dict]:
    """Add a message to conversation history."""
    history.append({
        "role": role,
        "content": content,
        "timestamp": datetime.now(timezone.utc).isoformat()
    })
    return history


def build_context_summary(history: List[Dict], max_messages: int = 20) -> str:
    """Build a context summary from conversation history for RAG."""
    if not history:
        return ""

    recent = history[-max_messages:] if len(history) > max_messages else history

    lines = []
    for msg in recent:
        role = "User" if msg["role"] == "user" else "Assistant"
        # Truncate long messages in context
        content = msg['content'][:500] + "..." if len(msg['content']) > 500 else msg['content']
        lines.append(f"{role}: {content}")

    return "\n".join(lines)


def extract_text(msg: ChatMessage) -> str:
    """Extract text content from a ChatMessage."""
    for item in msg.content:
        if isinstance(item, TextContent):
            return item.text
    return ""


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


# ============== Optimized System Prompt ==============

SYSTEM_PROMPT = """You are an expert job search assistant with real-time web search capabilities. Your primary goal is to find relevant, currently active job listings and provide accurate, actionable information.

## CORE RESPONSIBILITIES:
1. Search for job listings from reputable job boards (LinkedIn, Indeed, Naukri, Glassdoor, company career pages)
2. Provide ONLY verified, currently active job postings with working apply links
3. Understand conversation context for follow-up queries
4. Filter and rank jobs based on user preferences

## QUERY UNDERSTANDING:
- "show me more" / "more jobs" = Find additional jobs matching previous criteria
- "similar but remote" = Same role/skills, add remote filter
- "same in [city]" = Same criteria, different location
- "higher salary" / "better paying" = Similar roles with higher compensation
- "entry level" / "senior" = Adjust experience requirements
- "tell me about job #X" = Provide detailed info about specific listing

## OUTPUT FORMAT (STRICTLY FOLLOW):
For each job, use this exact format:

---
**Job #[number]**
**Title:** [Exact job title]
**Company:** [Company name]
**Location:** [City, State/Country] | [Remote/Hybrid/On-site]
**Experience:** [X-Y years] or [Entry Level/Mid/Senior]
**Skills:** [Comma-separated key skills]
**Salary:** [Salary range if available, otherwise "Not disclosed"]
**Posted:** [Date or "Recently posted"]
**Source:** [Job board name]
**Apply Link:** [FULL clickable URL - must be valid]

**Description:** [2-3 sentence summary of role and responsibilities]

---

## IMPORTANT RULES:
1. ALWAYS include the complete apply URL - never truncate or use placeholders
2. If no jobs found, suggest alternative search terms or related roles
3. Prioritize jobs posted within last 7 days when possible
4. Include mix of company sizes (startups, mid-size, enterprises)
5. Verify links are from legitimate job sources
6. If user asks non-job-related questions, politely redirect to job search
7. For follow-up queries, explicitly reference what changed from previous search

## RESPONSE GUIDELINES:
- List 5-10 relevant jobs per search
- Start response with brief summary: "Found X jobs matching [criteria]..."
- End with helpful suggestion: "Want me to refine by [salary/location/experience]?"
- If results are limited, explain why and suggest alternatives"""


# ============== Query Classification ==============

def classify_query(query: str, history: List[Dict]) -> Dict[str, Any]:
    """Classify the user query type for better handling."""
    query_lower = query.lower().strip()

    # Remove agent address mentions from query for better classification
    # Pattern: @agent1q... (agent addresses start with agent1q)
    query_clean = re.sub(r'@agent1q\w+', '', query_lower).strip()

    classification = {
        "type": "new_search",
        "is_followup": len(history) > 0,
        "modifiers": [],
        "needs_web_search": True  # Default: needs web search
    }

    # Context-based analysis patterns (NO web search needed - use conversation history)
    context_analysis_patterns = [
        # Summarization
        "summarize", "summary", "summarise", "sum up",
        # Extraction
        "extract", "list out", "list the", "what are the",
        # Analysis
        "analyze", "analyse", "compare", "comparison",
        # Shortlisting
        "shortlist", "short list", "top 2", "top 3", "top two", "top three", "best", "recommend",
        # Skills/tools extraction
        "key skills", "skills mentioned", "tools mentioned", "technologies", "tech stack",
        # Explanation
        "explain why", "why these", "why this", "reason",
        # From results
        "from these", "from the results", "from above", "based on these", "from previous",
        "across these", "in these jobs", "mentioned in",
        # Questions about previous results
        "which one", "which job", "what company", "how many",
    ]

    # Check if it's a context analysis query (no web search needed)
    for pattern in context_analysis_patterns:
        if pattern in query_clean:
            classification["type"] = "context_analysis"
            classification["needs_web_search"] = False
            classification["modifiers"].append(pattern)
            return classification

    # Follow-up patterns that need NEW web search
    followup_patterns = {
        "more_results": ["show me more", "more jobs", "more options", "any more", "additional jobs", "keep searching"],
        "refine_remote": ["remote", "work from home", "wfh", "remote only", "fully remote"],
        "refine_location": ["in bangalore", "in mumbai", "in delhi", "in hyderabad", "in pune", "in chennai", "in india", "in usa", "in us", "in uk"],
        "refine_salary": ["higher salary", "better pay", "more salary", "salary above", "paying more"],
        "refine_experience": ["entry level", "fresher", "senior", "junior", "lead", "manager", "experienced"],
        "job_detail": ["tell me more about", "details of", "more info on", "job #", "first job", "second job"],
    }

    for pattern_type, patterns in followup_patterns.items():
        for pattern in patterns:
            if pattern in query_clean:
                classification["type"] = pattern_type
                classification["modifiers"].append(pattern)
                break

    return classification


# ============== Context Analysis System Prompt ==============

CONTEXT_ANALYSIS_PROMPT = """You are a helpful job search assistant analyzing conversation history.

Your task is to answer the user's question based ONLY on the job listings and information already provided in the conversation history.

DO NOT search for new jobs. DO NOT make up information. Only use what's in the conversation.

When analyzing jobs from the conversation:
- Reference specific job titles, companies, and details mentioned
- Provide clear, structured analysis
- If asked to shortlist, explain your reasoning
- If asked about skills/tools, extract them from the job descriptions provided
- Be specific and reference the actual jobs discussed

If the conversation doesn't contain enough information to answer, say so clearly."""


# ============== Job Search and Analysis Functions ==============

async def analyze_context(query: str, history: List[Dict]) -> str:
    """
    Analyze conversation history to answer context-based questions.
    NO web search - uses only existing conversation data.
    """
    # Build messages with full conversation history
    messages = [{"role": "system", "content": CONTEXT_ANALYSIS_PROMPT}]

    # Add FULL conversation history for context analysis (not truncated)
    for msg in history:
        messages.append({
            "role": msg["role"],
            "content": msg["content"]  # Full content for analysis
        })

    # Clean query (remove agent address)
    clean_query = re.sub(r'@agent1q\w+\s*', '', query).strip()

    # Add current query with explicit instructions
    analysis_query = f"""Based on the conversation history above, please answer this question:

**User Question:** {clean_query}

**Instructions:**
- Answer using ONLY information from the previous messages in this conversation
- Reference specific job titles, companies, skills, and details mentioned earlier
- If asked to shortlist or recommend, explain your reasoning based on the user's stated preferences
- If asked about skills/tools, extract them directly from the job descriptions provided
- Be specific and accurate - do not make up information
- If you cannot answer from the conversation history, say so"""

    messages.append({"role": "user", "content": analysis_query})

    try:
        response = client.chat.completions.create(
            model="asi1",
            messages=messages,
            temperature=0.2,
            top_p=0.9,
            max_tokens=1000,
            presence_penalty=0,
            frequency_penalty=0,
            stream=False,
            extra_body={"web_search": False}
        )
        if response.choices and len(response.choices) > 0:
            return response.choices[0].message.content
        return "I couldn't analyze the conversation. Please try rephrasing your question."
    except Exception:
        return "An error occurred while analyzing. Please try again."


async def search_jobs_with_context(query: str, history: List[Dict]) -> str:
    """
    Search for jobs using the ASI1 API with optimized prompts.
    Includes conversation history for context-aware searches.
    """
    # Classify the query
    classification = classify_query(query, history)

    # If it's a context analysis query, use analyze_context instead
    if classification["type"] == "context_analysis":
        return await analyze_context(query, history)

    # Build messages array for job search
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    # Add conversation history (last 6 exchanges for context)
    for msg in history[-12:]:
        messages.append({
            "role": msg["role"],
            "content": msg["content"][:1500]  # Increased for better context
        })

    # Clean query (remove agent address)
    clean_query = re.sub(r'@agent1q\w+\s*', '', query).strip()

    # Build optimized user query based on classification
    if classification["is_followup"] and classification["type"] != "new_search":
        enhanced_query = build_followup_query(clean_query, classification, history)
    else:
        enhanced_query = build_initial_query(clean_query)

    messages.append({"role": "user", "content": enhanced_query})

    try:
        response = client.chat.completions.create(
            model="asi1",
            messages=messages,
            temperature=0.2,
            top_p=0.9,
            max_tokens=1000,
            presence_penalty=0,
            frequency_penalty=0,
            stream=False,
            extra_body={"web_search": True}
        )
        if response.choices and len(response.choices) > 0:
            return process_job_response(response.choices[0].message.content)
        return "No job listings found. Try adjusting your search criteria or check back later."
    except asyncio.TimeoutError:
        return "Search is taking longer than expected. Try a more specific query (e.g., add location or specific skills)."
    except Exception:
        return "An unexpected error occurred. Please try again with a different query."


def build_initial_query(query: str) -> str:
    """Build an optimized initial search query."""
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    return f"""Search for job listings matching this request:

**User Query:** {query}

**Search Instructions:**
1. Search major job boards: LinkedIn Jobs, Indeed, Naukri, Glassdoor, and company career pages
2. Focus on jobs posted within the last 7 days (today is {today})
3. Include the COMPLETE apply URL for each job - this is critical
4. Provide 5-10 most relevant results
5. If the query mentions "last 24 hours" or "today", prioritize very recent postings

**Required Output:** Follow the exact format specified in system instructions. Each job MUST have a working apply link."""


def build_followup_query(query: str, classification: Dict[str, Any], history: List[Dict]) -> str:
    """Build an optimized follow-up query based on context."""

    # Extract previous search context
    prev_context = ""
    for msg in reversed(history):
        if msg["role"] == "user":
            prev_context = msg["content"][:300]
            break

    query_type = classification["type"]
    modifiers = ", ".join(classification["modifiers"])

    followup_instructions = {
        "more_results": f"Find MORE job listings similar to the previous search. Show DIFFERENT jobs not already listed. Previous criteria: {prev_context}",
        "refine_remote": f"Search for REMOTE/Work-from-home versions of the previous job search. Previous criteria: {prev_context}",
        "refine_location": f"Search for jobs with the SAME criteria but in the NEW LOCATION mentioned. Original search: {prev_context}",
        "refine_salary": f"Find HIGHER PAYING jobs matching the previous criteria. Previous search: {prev_context}",
        "refine_experience": f"Adjust experience level as requested while keeping other criteria. Previous search: {prev_context}",
        "job_detail": f"Provide detailed information about the specific job the user is asking about from the previous results.",
    }

    instruction = followup_instructions.get(query_type, f"Process this follow-up request in context of previous search: {prev_context}")

    return f"""**Follow-up Query:** {query}

**Query Type:** {query_type}
**Modifiers Detected:** {modifiers}

**Instructions:** {instruction}

**Important:**
- Reference the previous conversation context
- Clearly indicate what changed from the previous search
- Include complete apply URLs for all jobs
- Maintain the standard output format"""


def process_job_response(response: str) -> str:
    """Process and validate the job search response."""
    if not response or len(response.strip()) < 50:
        return "No relevant jobs found for your criteria. Try:\n- Broadening your search terms\n- Removing specific requirements\n- Checking different locations"

    # Basic validation - check if response has job-like content
    job_indicators = ["apply", "company", "location", "experience", "salary", "http", "www"]
    has_jobs = any(indicator in response.lower() for indicator in job_indicators)

    if not has_jobs:
        return f"{response}\n\nNote: If you're not seeing relevant results, try being more specific about the role, location, or required skills."

    return response


def format_job_response(jobs_text: str) -> str:
    """Format the job search response - clean output without decorations."""
    return jobs_text


# ============== Chat Handlers ==============

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

        # Get or create session ID
        session_id = str(ctx.session) if hasattr(ctx, "session") and ctx.session else f"{sender}_{int(datetime.now(timezone.utc).timestamp())}"
        ctx.logger.info(f"Session ID: {session_id}")

        # Load session data from storage
        session_data = get_session_data(ctx, sender, session_id)
        history = session_data["history"]
        state = session_data["state"]

        # Extract text from the message
        text = extract_text(msg)

        # Handle non-text messages (session start/end)
        if not text:
            for item in msg.content:
                if isinstance(item, StartSessionContent):
                    ctx.logger.info(f"Session started with {sender}")
                    state["greeted"] = True
                    session_data["state"] = state
                    save_session_data(ctx, sender, session_id, session_data)

                    welcome_message = """Welcome to Job Search Agent!

I can help you find jobs based on your requirements. I remember our conversation, so you can:
- Ask follow-up questions like "show me similar jobs but remote"
- Refine searches: "same skills but in Bangalore"
- Reference previous results: "tell me more about the first job"

Example queries:
- 'Backend developer jobs in India using Python and FastAPI'
- 'Remote React developer positions posted this week'
- 'Data Science jobs with 2+ years experience'

What kind of job are you looking for?"""

                    await ctx.send(sender, create_text_chat(welcome_message))
                    return

                elif isinstance(item, EndSessionContent):
                    ctx.logger.info(f"Session ended with {sender}")
                    # Save final session state
                    save_session_data(ctx, sender, session_id, session_data)
                    await ctx.send(
                        sender,
                        create_text_chat(
                            "Thank you for using Job Search Agent!\n"
                            "Your conversation history has been saved.\n"
                            "Good luck with your job search!",
                            end_session=True
                        )
                    )
                    return
            return

        ctx.logger.info(f"Query: {text[:100]}")

        # Add user message to history
        history = add_to_history(history, "user", text)

        # Classify query for context-aware search
        classification = classify_query(text, history[:-1])
        ctx.logger.info(f"Query classification: {classification['type']}")

        # Search for jobs with context (pass history without current message)
        job_results = await search_jobs_with_context(text, history[:-1])

        ctx.logger.info(f"Result: {job_results[:200]}")

        # Format and prepare response
        formatted_results = format_job_response(job_results)

        # Add assistant response to history
        history = add_to_history(history, "assistant", job_results)

        # Save updated session data
        session_data["history"] = history
        session_data["state"] = state
        save_session_data(ctx, sender, session_id, session_data)

        # Send the response with retry logic
        max_retries = 3
        for attempt in range(max_retries):
            try:
                await ctx.send(sender, create_text_chat(formatted_results))
                ctx.logger.info(f"Sent response to {sender}")
                break
            except Exception as send_err:
                ctx.logger.warning(f"Send attempt {attempt + 1}/{max_retries} failed: {send_err}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(2 * (attempt + 1))
                else:
                    ctx.logger.error(f"All {max_retries} send attempts failed for {sender}")
                    raise

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
