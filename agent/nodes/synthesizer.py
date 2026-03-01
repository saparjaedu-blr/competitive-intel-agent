from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from agent.state import AgentState, CompetitorSynthesis
from config.settings import OPENAI_API_KEY, OPENAI_MODEL

llm = ChatOpenAI(model=OPENAI_MODEL, api_key=OPENAI_API_KEY, temperature=0.2)

SYSTEM_PROMPT = """You are a senior competitive intelligence analyst for a B2B SaaS product team.
Your job is to produce a deep, technically detailed competitive analysis — not surface-level summaries.

Rules:
- Be specific. Name actual features, protocols, UI patterns, and use cases found in the content.
- Never make generic statements like "they have a strong product" without backing it with specifics.
- If something is not mentioned in the source content, say "Not found in available sources" — do not hallucinate.
- When images are provided (UI screenshots, diagrams, pricing tables, roadmap slides), extract every 
  visible detail — button labels, menu items, field names, workflow steps, error states, data formats.
- Prioritize technical depth over breadth. A PM reading this should walk away knowing exactly how 
  this competitor works and where they are strong or weak."""

SYNTHESIS_PROMPT = """
Competitor: {vendor_name}
Research Focus: {research_query}

=== WEBSITE & BLOG CONTENT ===
{web_content}

=== PRODUCT DOCUMENTATION & CHANGELOG ===
{docs_content}

=== YOUTUBE VIDEO TRANSCRIPTS ===
{youtube_content}

=== PERSONAL SCRAPBOOK NOTES & IMAGES ===
{scrapbook_content}

{image_note}
---
Produce a DEEP competitive intelligence report with the following sections.
Be specific, technical, and grounded in the actual source content above.

## Recent Feature Launches & Updates
List every specific feature, update, or announcement found. Include:
- Feature name and what it does
- When it was launched (if mentioned)
- Which customer segment it targets
- Any technical implementation details mentioned

## Use Cases & Target Segments
- What specific problems does this vendor solve, and for whom?
- List concrete use cases with details (e.g. "real-time inventory sync for D2C brands", not just "inventory management")
- Which industries or company sizes do they explicitly target?
- What workflows or jobs-to-be-done do their case studies and docs highlight?

## Technical Architecture & Protocol Support
- What APIs, protocols, or standards do they support? (REST, GraphQL, WebSockets, MQTT, OAuth, SAML, etc.)
- What are their integration capabilities? (native connectors, webhooks, SDKs, iPaaS support)
- What are their infrastructure or deployment options? (cloud, on-prem, multi-tenant, SOC2, GDPR, etc.)
- Any technical limitations, known constraints, or deprecations mentioned?
- What data formats do they work with? (JSON, XML, CSV, Parquet, etc.)

## User Interface & User Experience
- Describe the UI paradigm — is it wizard-based, drag-and-drop, code-first, dashboard-centric?
- What specific UI components or workflows are visible in screenshots or described in docs?
- How do they handle onboarding, empty states, or first-run experience?
- Any notable UX patterns — inline editing, bulk actions, keyboard shortcuts, templates?
- Mobile or accessibility support mentioned?

## Pricing & Packaging
- List specific pricing tiers with names, prices, and what's included if available
- What are the usage limits or metering dimensions? (seats, API calls, records, events)
- Any freemium, trial, or PLG motion?
- Enterprise vs. self-serve split — how do they draw that line?
- Any recent pricing changes or signals?

## Strategic Direction & Roadmap Signals
- Where does this vendor appear to be headed in the next 6-12 months?
- What themes dominate their recent blog posts, conference talks, and release notes?
- Any acquisitions, partnerships, or platform bets mentioned?
- What problems are they visibly investing in solving next?

## Gaps vs Your Product
- What capabilities does this vendor have that may be ahead of your product? Be specific.
- Where are they clearly weaker or missing functionality?
- What do their negative reviews or support issues reveal about pain points?
- What is your best differentiation opportunity based on this analysis?

## Key Watch Points
Top 3-5 specific things to monitor about this vendor in the next quarter, with reasoning.
"""


def _build_multimodal_message(prompt_text: str, images_base64: list[str]) -> HumanMessage:
    """Build a HumanMessage with text + images for GPT-4o vision input."""
    if not images_base64:
        return HumanMessage(content=prompt_text)

    content_blocks = [{"type": "text", "text": prompt_text}]
    for b64 in images_base64:
        content_blocks.append({
            "type": "image_url",
            "image_url": {
                "url": f"data:image/png;base64,{b64}",
                "detail": "high",
            },
        })
    return HumanMessage(content=content_blocks)


def synthesizer_node(state: AgentState) -> AgentState:
    """
    Call GPT-4o to synthesize raw data (text + images) into deep structured intelligence per vendor.
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
            item.get("docs_content", "") +
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
                f"{len(scrapbook_images)} image(s) attached below. Analyze every visible detail — "
                f"UI elements, field names, workflows, pricing tables, roadmap slides, diagrams.\n"
                if has_images else ""
            )

            prompt = SYNTHESIS_PROMPT.format(
                vendor_name=vendor_name,
                research_query=research_query,
                web_content=item.get("web_content", "Not available")[:4000],
                docs_content=item.get("docs_content", "Not available")[:4000],
                youtube_content=item.get("youtube_content", "Not available")[:3000],
                scrapbook_content=item.get("scrapbook_content", "Not available")[:2000],
                image_note=image_note,
            )

            human_msg = _build_multimodal_message(prompt, scrapbook_images)

            response = llm.invoke([
                SystemMessage(content=SYSTEM_PROMPT),
                human_msg,
            ])

            raw_synthesis = response.content

            synthesis: CompetitorSynthesis = {
                "vendor_name": vendor_name,
                "recent_launches": _extract_section(raw_synthesis, "Recent Feature Launches"),
                "use_cases": _extract_section(raw_synthesis, "Use Cases"),
                "technical_details": _extract_section(raw_synthesis, "Technical Architecture"),
                "ui_ux": _extract_section(raw_synthesis, "User Interface"),
                "pricing_signals": _extract_section(raw_synthesis, "Pricing & Packaging"),
                "strategic_direction": _extract_section(raw_synthesis, "Strategic Direction"),
                "gap_vs_your_product": _extract_section(raw_synthesis, "Gaps vs Your Product"),
                "watch_points": _extract_section(raw_synthesis, "Key Watch Points"),
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
