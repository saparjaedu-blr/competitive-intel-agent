from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage, SystemMessage
from agent.state import AgentState, CompetitorSynthesis
from config.settings import OPENAI_API_KEY, OPENAI_MODEL

llm = ChatOpenAI(model=OPENAI_MODEL, api_key=OPENAI_API_KEY, temperature=0.2)

SYSTEM_PROMPT = """You are a senior competitive intelligence analyst for a B2B SaaS product team.
Your job is to synthesize raw intelligence about a competitor and produce a structured, 
actionable report tailored to a specific research focus. Be specific — avoid generic statements.
Always ground your observations in the actual content provided."""

SYNTHESIS_PROMPT = """
Competitor: {vendor_name}
Research Focus: {research_query}

=== WEBSITE & BLOG CONTENT ===
{web_content}

=== YOUTUBE VIDEO TRANSCRIPTS ===
{youtube_content}

=== PERSONAL SCRAPBOOK NOTES ===
{scrapbook_content}

---
Based on the above, provide a structured analysis in this exact format:

## Recent Feature Launches & Updates
[What has this vendor shipped recently? Be specific with feature names if mentioned.]

## Pricing Signals
[Any pricing changes, new tiers, freemium moves, or enterprise positioning signals?]

## Strategic Direction
[Where does this vendor appear to be headed in the next 6-12 months based on their messaging, 
launches, conference talks, and blog focus?]

## Gaps vs Your Product
[Based on this research, what capabilities does this vendor have that may be ahead of your product? 
What are they NOT doing well that could be a competitive advantage for you?]

## Key Watch Points
[Top 3 things to monitor closely about this vendor in the next quarter.]
"""


def synthesizer_node(state: AgentState) -> AgentState:
    """
    Call GPT-4o to synthesize raw data into structured intelligence per vendor.
    """
    raw_data = state.get("raw_data", [])
    research_query = state.get("research_query", "General competitive overview")
    syntheses: list[CompetitorSynthesis] = []
    errors = state.get("errors", [])

    for item in raw_data:
        vendor_name = item["vendor_name"]

        # Skip vendors with no data at all
        total_content = (
            item.get("web_content", "") +
            item.get("youtube_content", "") +
            item.get("scrapbook_content", "")
        )
        if not total_content.strip():
            errors.append(f"No content retrieved for {vendor_name} — skipping synthesis.")
            continue

        try:
            prompt = SYNTHESIS_PROMPT.format(
                vendor_name=vendor_name,
                research_query=research_query,
                web_content=item.get("web_content", "Not available")[:4000],
                youtube_content=item.get("youtube_content", "Not available")[:3000],
                scrapbook_content=item.get("scrapbook_content", "Not available")[:2000],
            )

            response = llm.invoke([
                SystemMessage(content=SYSTEM_PROMPT),
                HumanMessage(content=prompt),
            ])

            raw_synthesis = response.content

            # Parse sections from the markdown response
            synthesis: CompetitorSynthesis = {
                "vendor_name": vendor_name,
                "recent_launches": _extract_section(raw_synthesis, "Recent Feature Launches"),
                "pricing_signals": _extract_section(raw_synthesis, "Pricing Signals"),
                "strategic_direction": _extract_section(raw_synthesis, "Strategic Direction"),
                "gap_vs_your_product": _extract_section(raw_synthesis, "Gaps vs Your Product"),
                "raw_synthesis": raw_synthesis,
            }
            syntheses.append(synthesis)

        except Exception as e:
            errors.append(f"Synthesis failed for {vendor_name}: {str(e)}")

    return {
        **state,
        "syntheses": syntheses,
        "errors": errors,
        "current_step": "synthesis_complete",
    }


def _extract_section(text: str, section_title: str) -> str:
    """Extract content under a specific ## heading."""
    lines = text.split("\n")
    capturing = False
    result = []

    for line in lines:
        if section_title.lower() in line.lower() and line.startswith("##"):
            capturing = True
            continue
        if capturing:
            if line.startswith("##"):
                break
            result.append(line)

    return "\n".join(result).strip()
