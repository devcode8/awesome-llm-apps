import asyncio
import os
import re
from logging import Logger
from typing import Callable

import httpx
from async_lru import alru_cache
from bs4 import BeautifulSoup
from langchain.agents import create_agent  # pyright: ignore[reportUnknownVariableType]
from langchain.tools import tool  # pyright: ignore[reportUnknownVariableType]
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.config import get_stream_writer
from pydantic import SecretStr

# ─────────────────────────────────────────────────────────────────────────────
# 1.  Environment helpers
# ─────────────────────────────────────────────────────────────────────────────


def _load_env(var: str) -> str:
    value = os.getenv(var)
    if not value:
        raise EnvironmentError(f"Environment variable '{var}' is required but not set.")
    return value


def _load_env_secret(var: str) -> SecretStr:
    return SecretStr(_load_env(var))


# ─────────────────────────────────────────────────────────────────────────────
# 2.  Shared HTTP client
# ─────────────────────────────────────────────────────────────────────────────

_http_client = httpx.AsyncClient(timeout=10.0, follow_redirects=True)

# ─────────────────────────────────────────────────────────────────────────────
# 3.  HTML / URL helpers
# ─────────────────────────────────────────────────────────────────────────────

LEGAL_LINK_KEYWORDS = {
    "privacy",
    "policy",
    "legal",
    "agreement",
    "terms",
    "arbitration",
    "subscription",
    "refund",
    "dpa",
}

_STRIP_TAGS = {"script", "style", "nav", "footer", "header", "noscript"}


def _clean_html(html: str) -> str:
    """Strip boilerplate tags and return plain text."""
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(_STRIP_TAGS):
        tag.decompose()
    return soup.get_text(separator="\n", strip=True)


def _extract_legal_links(html: str, base_url: str) -> list[str]:
    """Return up to 5 same-domain legal-relevant links (depth-1 only)."""
    from urllib.parse import urljoin, urlparse

    base_domain = urlparse(base_url).netloc
    soup = BeautifulSoup(html, "html.parser")
    seen: set[str] = set()
    links: list[str] = []

    for a in soup.find_all("a", href=True):
        href = str(a["href"]).strip()
        text = (a.get_text() + " " + href).lower()

        if not any(kw in text for kw in LEGAL_LINK_KEYWORDS):
            continue

        full = urljoin(base_url, href)
        parsed = urlparse(full)

        if parsed.netloc != base_domain:
            continue
        if parsed.scheme not in ("http", "https"):
            continue
        if full in seen:
            continue

        seen.add(full)
        links.append(full)
        if len(links) >= 5:
            break

    return links


# ─────────────────────────────────────────────────────────────────────────────
# 4.  Tools
# ─────────────────────────────────────────────────────────────────────────────


# ── 4a. fetch_contract_from_url ───────────────────────────────────────────────


@alru_cache(maxsize=64)
async def _fetch_contract_impl(url: str) -> str:
    """Cached fetch + merge of all legal content from a URL."""
    from urllib.parse import urlparse

    writer = get_stream_writer()

    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        return "ERROR: Only HTTP/HTTPS URLs are supported."

    writer(f"🌐 Connecting to {url} …")

    try:
        resp = await _http_client.get(url)
        resp.raise_for_status()
    except Exception as exc:
        return f"ERROR: Could not fetch URL — {exc}"

    writer("🧹 Cleaning HTML — stripping scripts, navbars, footers …")
    raw_html = resp.text
    main_text = _clean_html(raw_html)

    if len(main_text) < 500:
        return "ERROR: Insufficient legal content detected at this URL."

    writer(f"✅ Main page extracted — {len(main_text):,} characters")

    sources = [url]
    all_text = f"=== SOURCE: {url} ===\n{main_text}"

    writer("🔗 Scanning for linked legal pages (privacy, refund, DPA …) …")
    linked_urls = _extract_legal_links(raw_html, url)

    if linked_urls:
        writer(f"📄 Found {len(linked_urls)} linked legal page(s) — fetching …")
    else:
        writer("ℹ️ No linked legal pages found — continuing with main content only")

    for i, linked_url in enumerate(linked_urls, 1):
        if linked_url in sources:
            writer(f"  ↳ [{i}/{len(linked_urls)}] Skipped duplicate {linked_url}")
            continue
        writer(f"  ↳ [{i}/{len(linked_urls)}] Fetching {linked_url} …")
        try:
            linked_resp = await _http_client.get(linked_url)
            linked_resp.raise_for_status()
            linked_text = _clean_html(linked_resp.text)
            if len(linked_text) >= 300:
                sources.append(linked_url)
                all_text += f"\n\n=== SOURCE: {linked_url} ===\n{linked_text}"
                writer(f"  ✅ Merged — {len(linked_text):,} characters")
            else:
                writer("  ⚠️ Skipped — content too short")
        except Exception as exc:
            writer(f"  ❌ Could not fetch: {exc}")

    sources_list = "\n".join(f"  - {s}" for s in sources)
    writer(
        f"📦 Ready — {len(sources)} source(s), {len(all_text):,} total characters\nGenerating report..."
    )
    return f"SOURCES ANALYZED:\n{sources_list}\n\nCONTRACT CONTENT:\n{all_text}"


@tool
async def fetch_contract_from_url(url: str) -> str:
    """Fetch and clean legal contract/terms text from a URL.

    Discovers up to 5 same-domain legal-related linked pages (privacy policy,
    refund policy, DPA, etc.) and merges them into a single text block.
    Returns combined plain-text with source markers, or an error message if
    insufficient content is found. Results are cached — repeat calls with the
    same URL return instantly without re-fetching.

    Args:
        url: Full HTTP/HTTPS URL of the terms or contract page to analyse.
    """
    return await _fetch_contract_impl(url)


# ── 4b. prepare_raw_contract_text ────────────────────────────────────────────


@alru_cache(maxsize=64)
async def _prepare_raw_impl(raw_text: str) -> str:
    """Cached clean + validation of pasted contract text."""
    writer = get_stream_writer()

    writer("🔍 Inspecting input — checking for HTML markup …")

    if re.search(r"<[a-zA-Z][\s\S]*?>", raw_text):
        writer("🧹 HTML detected — stripping tags …")
        cleaned = _clean_html(raw_text)
        writer(f"✅ HTML cleaned — {len(cleaned):,} characters of plain text")
    else:
        cleaned = raw_text.strip()
        writer(f"✅ Plain text received — {len(cleaned):,} characters")

    if len(cleaned) < 500:
        return (
            "ERROR: Text is too short to be a valid contract (minimum 500 characters)."
        )

    writer("🔗 Scanning for embedded URLs …")
    urls_found = re.findall(r"https?://[^\s\"'<>]+", raw_text)[:3]
    extra_text = ""

    if urls_found:
        writer(f"📎 Found {len(urls_found)} embedded URL(s) — fetching …")
        for i, emb_url in enumerate(urls_found, 1):
            writer(f"  ↳ [{i}/{len(urls_found)}] Fetching {emb_url} …")
            try:
                resp = await _http_client.get(emb_url)
                resp.raise_for_status()
                fetched = _clean_html(resp.text)
                if len(fetched) >= 300:
                    extra_text += f"\n\n=== EMBEDDED SOURCE: {emb_url} ===\n{fetched}"
                    writer(f"  ✅ Merged {len(fetched):,} characters from {emb_url}")
                else:
                    writer("  ⚠️ Skipped — too short")
            except Exception as exc:
                writer(f"  ❌ Could not fetch {emb_url}: {exc}")
    else:
        writer("ℹ️ No embedded URLs found — using provided text only")

    writer("✅ Text preparation complete")
    return (
        f"SOURCES ANALYZED:\n  - [raw text provided by user]\n\n"
        f"CONTRACT CONTENT:\n{cleaned}{extra_text}"
    )


@tool
async def prepare_raw_contract_text(raw_text: str) -> str:
    """Clean and validate raw contract text supplied directly by the user.

    Strips HTML if present, validates minimum length (500 characters), and
    optionally fetches any embedded URLs (up to 3) to enrich the analysis.
    Results are cached — identical inputs return instantly on repeat calls.

    Args:
        raw_text: The raw contract or terms text (may include HTML markup
                  or embedded URL references).
    """
    return await _prepare_raw_impl(raw_text)


# ── 4c. is_legal_content ─────────────────────────────────────────────────────


@alru_cache(maxsize=128)
async def _is_legal_impl(text_sample: str) -> str:
    """Cached keyword-based legal content pre-check."""
    writer = get_stream_writer()

    writer("🔎 Running legal content pre-check …")

    legal_signals = [
        "terms",
        "agreement",
        "privacy",
        "policy",
        "clause",
        "liability",
        "indemnif",
        "arbitration",
        "governing law",
        "jurisdiction",
        "refund",
        "subscription",
        "intellectual property",
        "warranty",
        "disclaimer",
        "limitation",
        "terminate",
        "consent",
        "data processing",
    ]
    sample_lower = text_sample.lower()
    matched = [sig for sig in legal_signals if sig in sample_lower]
    count = len(matched)
    preview = ", ".join(matched[:6]) + ("…" if count > 6 else "")

    writer(f"📊 {count}/{len(legal_signals)} legal signals matched: {preview}")

    if count >= 3:
        writer("✅ Legal document confirmed")
        return "YES"
    if count == 0:
        writer("❌ No legal terminology found")
        return "NO: No legal terminology detected. This does not appear to be a legal document."

    writer(f"⚠️ Only {count} signal(s) — uncertain")
    return (
        f"UNCERTAIN: Only {count} legal signal(s) detected. "
        "Please verify whether this is a legal agreement before full analysis."
    )


@tool
async def is_legal_content(text_sample: str) -> str:
    """Quick pre-check: determine whether a block of text is a legal agreement or policy.

    Returns 'YES', 'NO: <reason>', or 'UNCERTAIN: <detail>'.
    Call this BEFORE clause extraction when content origin is uncertain.
    Results are cached.

    Args:
        text_sample: Up to 3000 characters of the content to classify.
    """
    return await _is_legal_impl(text_sample)


# ── 4d. extract_and_analyse_clauses ──────────────────────────────────────────


@alru_cache(maxsize=32)
async def _extract_impl(contract_text: str) -> str:
    """Cached pass-through that delivers contract text to the LLM."""
    writer = get_stream_writer()

    char_count = len(contract_text)
    writer(f"📋 Contract loaded — {char_count:,} characters")

    rough_sections = len(
        re.findall(
            r"(?:^|\n)\s*(?:\d+[\.\)]|[A-Z][A-Z\s]{2,}:|\#{1,3})\s+\w",
            contract_text,
        )
    )
    if rough_sections > 0:
        writer(
            f"🧩 ~{rough_sections} potential sections detected — extracting clauses …"
        )
    else:
        writer("🧩 Extracting clauses from contract …")

    writer("⚖️  Scoring risk levels per clause (low / medium / high) …")
    writer("📝 Writing summary …")

    preview = contract_text[:200].replace("\n", " ")
    return (
        f"ANALYSIS REQUEST RECEIVED.\n"
        f"Contract text length: {char_count} characters.\n"
        f"Preview: {preview}...\n\n"
        f"FULL CONTRACT TEXT FOR ANALYSIS:\n\n{contract_text}"
    )


@tool
async def extract_and_analyse_clauses(contract_text: str) -> str:
    """Perform deep clause extraction and risk analysis on prepared contract text.

    Delivers the contract to the LLM for open-ended clause discovery:
      - Identifies every logical clause/section boundary
      - Generates plain-English summaries and risk levels (low/medium/high)
      - Flags financial, arbitration, data, auto-renewal, termination clauses
      - Synthesises an overall risk level and concerns list
    Results are cached for identical contract texts.

    Args:
        contract_text: Cleaned, merged contract text (output of
                       fetch_contract_from_url or prepare_raw_contract_text).
    """
    return await _extract_impl(contract_text)


# ── 4e. format_risk_report ────────────────────────────────────────────────────


@alru_cache(maxsize=32)
async def _format_report_impl(
    title: str,
    jurisdiction: str,
    sources: str,
    clauses_markdown: str,
    overall_risk: str,
    major_concerns: str,
    precautions: str,
) -> str:
    """Cached final report assembly."""
    writer = get_stream_writer()

    writer("📊 Assembling risk report …")

    sources_block = "\n".join(
        f"- {s.strip()}" for s in sources.splitlines() if s.strip()
    )
    concerns_block = "\n".join(
        f"- {c.strip()}" for c in major_concerns.splitlines() if c.strip()
    )
    precautions_block = "\n".join(
        f"- {p.strip()}" for p in precautions.splitlines() if p.strip()
    )
    risk_emoji = {"low": "🟢", "moderate": "🟡", "high": "🔴"}.get(
        overall_risk.lower(), "⚪"
    )

    writer(f"🎨 Overall risk: {risk_emoji} {overall_risk.upper()}")
    writer("✅ Report ready")

    report = f"""# 🏛 Contract Risk Report: {title}

**Jurisdiction:** {jurisdiction}
**Sources:** {sources_block}

---

## Clauses

{clauses_markdown}

---

## Overall Risk: {risk_emoji} {overall_risk.upper()}

**Key Concerns**
{concerns_block}

**Recommended Actions**
{precautions_block}

---

> ⚠️ *AI-generated — informational only. Not legal advice. Consult a qualified attorney before signing.*
"""
    return report


@tool
async def format_risk_report(
    title: str,
    jurisdiction: str,
    sources: str,
    clauses_markdown: str,
    overall_risk: str,
    major_concerns: str,
    precautions: str,
) -> str:
    """Assemble the final human-readable risk report in Markdown format.

    Call this as the LAST step once all clauses have been analysed.
    Results are cached — same inputs return instantly.

    Args:
        title:             Contract/document title (e.g. "Acme SaaS Terms of Service").
        jurisdiction:      Governing law/jurisdiction, or "Not specified".
        sources:           Newline-separated list of sources analysed.
        clauses_markdown:  Full Markdown clause breakdown you generated.
        overall_risk:      One of: low | moderate | high
        major_concerns:    Newline-separated top concerns.
        precautions:       Newline-separated recommended user actions.
    """
    return await _format_report_impl(
        title,
        jurisdiction,
        sources,
        clauses_markdown,
        overall_risk,
        major_concerns,
        precautions,
    )


# ─────────────────────────────────────────────────────────────────────────────
# 5.  System prompt
# ─────────────────────────────────────────────────────────────────────────────

SYSTEM_PROMPT = """You are the **AI Contract Risk Scanner** — a precise, professional legal-document analysis agent.

## Your Mission
Analyse contracts, terms of service, privacy policies, and legal agreements.
Break them into clauses, flag risks, and deliver a clear, concise report.

---

## DEFAULT REPORT FORMAT — keep it scannable
Unless the user explicitly asks for a **detailed** or **full** report:
- Cover the **5-8 most important clauses** only (skip boilerplate like "Definitions" or "Notices" unless they're risky).
- Each clause entry: **one heading + 1-2 sentence summary + risk badge**. No lengthy reasoning paragraphs.
- Overall risk section: 3-5 bullet concerns + 3-5 bullet actions. Short and sharp.
- Target length: **under 600 words** for the full report.

If the user says "detailed", "full", "thorough", "complete", or "explain everything" → expand every clause with full reasoning.

---

## Workflow — follow this for every NEW contract:

**Step 1 — Acquire text**
- URL provided → `fetch_contract_from_url(url)`
- Raw text provided → `prepare_raw_contract_text(raw_text)`

**Step 2 — Pre-check** (only when content origin is uncertain)
- `is_legal_content(text_sample)` with the first ~2000 characters
- If "NO" → tell the user and stop

**Step 3 — Analyse**
- `extract_and_analyse_clauses(contract_text)`
- From the returned text, identify clauses yourself:
  - Risk levels: 🟢 **low** · 🟡 **medium** · 🔴 **high**
  - Always flag: financial exposure, data sharing, arbitration, auto-renewal, termination, liability caps

**Step 4 — Report**
- `format_risk_report(...)` → return the output verbatim

---

## Follow-up conversations
After the initial report, answer follow-up questions directly — no need to re-run tools unless new content is provided:

- *"Which clause is riskiest?"* → highlight it and explain briefly
- *"Summarise the report"* → 3-5 bullet TL;DR
- *"What does the arbitration clause mean?"* → plain-English explanation
- *"Give me the detailed/full report"* → re-run analysis at full depth
- *"Compare to standard terms"* → concise comparison
- *"Is this safe to sign?"* → honest assessment with appropriate caveats

---

## Risk Guidelines
Evaluate each clause on:
- **Power imbalance** — does the company hold all the cards?
- **User rights** — are legal remedies restricted?
- **Financial exposure** — hidden charges, no-refund, auto-renewal?
- **Data exposure** — broad collection or third-party sharing?
- **Legal waiver** — arbitration, class-action ban?
- **Clarity** — vague language that could be exploited?

## Tone
Direct, professional, plain English. Never fabricate clauses.
If content is truncated, note it clearly.
"""

# ─────────────────────────────────────────────────────────────────────────────
# 6.  Model + Agent construction
# ─────────────────────────────────────────────────────────────────────────────

ASI1_API_KEY = _load_env_secret("ASI1_API_KEY")
ASI1_MODEL = _load_env("ASI1_MODEL")
ASI1_BASE_URL = _load_env("ASI1_BASE_URL")

_model = ChatOpenAI(
    temperature=0.1,
    timeout=60,
    api_key=ASI1_API_KEY,
    base_url=ASI1_BASE_URL,
    model=ASI1_MODEL,
)

_tools = [
    fetch_contract_from_url,
    prepare_raw_contract_text,
    is_legal_content,
    extract_and_analyse_clauses,
    format_risk_report,
]

_checkpointer = InMemorySaver()

_agent = create_agent(  # pyright: ignore[reportUnknownVariableType]
    _model,
    tools=_tools,
    system_prompt=SYSTEM_PROMPT,
    checkpointer=_checkpointer,
)

# ─────────────────────────────────────────────────────────────────────────────
# 7.  Public chat() entry-point
# ─────────────────────────────────────────────────────────────────────────────


async def chat(
    session_id: str,
    message: str,
) -> str:
    result = await _agent.ainvoke(  # pyright: ignore[reportUnknownMemberType]
        {"messages": [{"role": "user", "content": message}]},
        config={"configurable": {"thread_id": session_id}},
        stream_mode=["updates", "custom"],
    )
    
    # Extract the final message content from the agent result
    final_response = ""
    for event_type, event_data in result:
        if event_type == "updates" and "model" in event_data:
            messages = event_data["model"].get("messages", [])
            if messages:
                final_response = messages[-1].content
                break
    
    if not final_response:
        final_response = (
            "⚠️ Analysis complete but no response was generated. Please try again."
        )

    return final_response
