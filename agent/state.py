from typing import TypedDict, List, Optional


class CompetitorRawData(TypedDict):
    vendor_name: str
    web_content: str              # scraped from website + blog
    docs_content: str             # scraped from product docs + changelog
    youtube_content: str          # transcripts concatenated
    scrapbook_content: str        # text extracted from Google Doc tabs
    scrapbook_images: List[str]   # base64 images extracted from Google Doc


class CompetitorSynthesis(TypedDict):
    vendor_name: str
    recent_launches: str
    use_cases: str                # NEW — specific use cases and target segments
    technical_details: str        # NEW — protocols, APIs, integrations, architecture
    ui_ux: str                    # NEW — UI patterns, UX observations, interface details
    pricing_signals: str
    strategic_direction: str
    gap_vs_your_product: str
    watch_points: str             # NEW — specific things to monitor next quarter
    raw_synthesis: str


class DiffResult(TypedDict):
    vendor_name: str
    delta_summary: str
    is_first_run: bool


class AgentState(TypedDict):
    # ── Inputs ────────────────────────────────
    vendors: List[str]
    research_query: str

    # ── Intermediate ──────────────────────────
    raw_data: List[CompetitorRawData]
    syntheses: List[CompetitorSynthesis]
    diffs: List[DiffResult]

    # ── Outputs ───────────────────────────────
    final_report_markdown: str
    gdrive_link: str

    # ── Meta ──────────────────────────────────
    errors: List[str]
    current_step: str
