from agent.state import AgentState
from agent.tools.youtube_tool import fetch_channel_transcripts
from db.database import get_competitor_by_name


def youtube_scraper_node(state: AgentState) -> AgentState:
    """
    Fetch YouTube transcripts for each vendor's channel.
    Updates youtube_content in raw_data.
    """
    vendors = state["vendors"]
    raw_data = {d["vendor_name"]: d for d in state.get("raw_data", [])}
    errors = state.get("errors", [])

    for vendor_name in vendors:
        competitor = get_competitor_by_name(vendor_name)
        if not competitor:
            continue

        channel = competitor.get("youtube_channel", "")
        youtube_content = fetch_channel_transcripts(channel, max_videos=5) if channel else ""

        if vendor_name in raw_data:
            raw_data[vendor_name]["youtube_content"] = youtube_content
        else:
            raw_data[vendor_name] = {
                "vendor_name": vendor_name,
                "web_content": "",
                "youtube_content": youtube_content,
                "scrapbook_content": "",
            }

    return {
        **state,
        "raw_data": list(raw_data.values()),
        "errors": errors,
        "current_step": "youtube_scraping_complete",
    }
