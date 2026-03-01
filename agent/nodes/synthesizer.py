from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from agent.state import AgentState, CompetitorSynthesis
from config.settings import OPENAI_API_KEY, OPENAI_MODEL

llm = ChatOpenAI(model=OPENAI_MODEL, api_key=OPENAI_API_KEY, temperature=0.2)

SYSTEM_PROMPT = """You are a senior competitive intelligence analyst for a B2B SaaS product team.
Your job is to synthesize raw intelligence about a competitor and produce a structured,
actionable report tailored to a specific research focus. Be specific — avoid generic statements.
Always ground your observations in the actual content provided.
When images are provided, analyze them carefully — they may contain UI screenshots, feature
comparisons, pricing tables, or roadmap visuals. Extract every relevant insight from them."""

SYNTHESIS_PROMPT = """
Competitor: {vendor_name}
Research Focus: {research_query}

=== WEBSITE & BLOG CONTENT ===
{web_content}

=== YOUTUBE VIDEO TRANSCRIPTS ===
{youtube_content}

=== PERSONAL SCRAPBOOK NOTES ===
{scrapbook_content}

{image_note}
---
Based on ALL of the above (text and any images provided), give a structured analysis:

## Recent Feature Launches & Updates
[What has this vendor shipped recently? Be specific with feature names if mentioned.]

## Pricing Signals
[Any pricing changes, new tiers, freemium moves, or enterprise positioning signals?]

## Strategic Direction
[Where does this vendor appear to be headed in the next 6-12 months?]

## Gaps vs Your Product
[What capabilities does this vendor have that may be ahead of your product?
What are they NOT doing well that could be a competitive advantage for you?]

## Key Watch Points
[Top 3 things to monitor closely about this vendor in the next quarter.]
"""


def _build_multimodal_message(prompt_text: str, images_base64: list[str]) -> HumanMessage:
    """
    Build a HumanMessage with text + images for GPT-4o vision input.
    Images are passed as base64-encoded JPEG/PNG data URIs.
    """
    if not images_base64:
        return HumanMessage(content=prompt_text)

    # Multimodal content: text block + one image block per image
    content_blocks = [{"type": "text", "text": prompt_text}]

    for b64 in images_base64:
        content_blocks.append({
            "type": "image_url",
            "image_url": {
                "url": f"data:image/png;base64,{b64}",
                "detail": "high",   # use "low" to save tokens if needed
            },
        })

    return HumanMessage(content=content_blocks)


def synthesizer_node(state: AgentState) -> AgentState:
    """
    Call GPT-4o to synthesize raw data (text + images) into structured intelligence per vendor.
    Images from the scrapbook Google Doc are passed directly to GPT-4o as vision input.
    """
    raw_data = state.get("raw_data", [])
    research_query = state.get("research_query", "General competitive overview")
    syntheses: list[CompetitorSynthesis] = []
    errors = state.get("errors", [])

    for item in raw_data:
        vendor_name = item["vendor_name"]
        scrapbook_images = item.get("scrapbook_images", [])

        total_content = (
            item.get("web_content", "") +
            item.get("youtube_content", "") +
            item.get("scrapbook_content", "")
        )
        has_images = len(scrapbook_images) > 0

        if not total_content.strip() and not has_images:
            errors.append(f"No content retrieved for {vendor_name} — skipping synthesis.")
            continue

        try:
            image_note = (
                f"\n=== SCRAPBOOK IMAGES ===\n"
                f"{len(scrapbook_images)} image(s) from the scrapbook are attached below. "
                f"Analyze them carefully for UI features, pricing tables, roadmap slides, "
                f"or any competitive signals.\n"
                if has_images else ""
            )

            prompt = SYNTHESIS_PROMPT.format(
                vendor_name=vendor_name,
                research_query=research_query,
                web_content=item.get("web_content", "Not available")[:4000],
                youtube_content=item.get("youtube_content", "Not available")[:3000],
                scrapbook_content=item.get("scrapbook_content", "Not available")[:2000],
                image_note=image_note,
            )

            # Build multimodal message — images attached if present
            human_msg = _build_multimodal_message(prompt, scrapbook_images)

            response = llm.invoke([
                SystemMessage(content=SYSTEM_PROMPT),
                human_msg,
            ])

            raw_synthesis = response.content

            synthesis: CompetitorSynthesis = {
                "vendor_name": vendor_name,
                "recent_launches": _extract_section(raw_synthesis, "Recent Feature Launches"),
                "pricing_signals": _extract_section(raw_synthesis, "Pricing Signals"),
                "strategic_direction": _extract_section(raw_synthesis, "Strategic Direction"),
                "gap_vs_your_product": _extract_section(raw_synthesis, "Gaps vs Your Product"),
                "raw_synthesis": raw_synthesis,
            }
            syntheses.append(synthesis)

            if has_images:
                errors.append(
                    f"✅ {vendor_name}: synthesized with {len(scrapbook_images)} scrapbook image(s)"
                )

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
