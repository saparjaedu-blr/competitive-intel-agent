from agent.state import AgentState
from agent.tools.scraper_tool import scrape_multiple
from db.database import get_competitor_by_name


def web_scraper_node(state: AgentState) -> AgentState:
    """
    Fetch and scrape website + blog content for each vendor.
    Updates raw_data in state.
    """
    vendors = state["vendors"]
    raw_data = state.get("raw_data", [])
    errors = state.get("errors", [])

    # Build a lookup for already-fetched vendors
    existing = {d["vendor_name"]: d for d in raw_data}

    for vendor_name in vendors:
        competitor = get_competitor_by_name(vendor_name)
        if not competitor:
            errors.append(f"Vendor '{vendor_name}' not found in database.")
            continue

        urls = [
            competitor.get("website_url", ""),
            competitor.get("blog_url", ""),
        ]
        urls = [u for u in urls if u]  # filter empty

        web_content = scrape_multiple(urls) if urls else ""

        # Merge into existing raw_data entry or create new
        if vendor_name in existing:
            existing[vendor_name]["web_content"] = web_content
        else:
            existing[vendor_name] = {
                "vendor_name": vendor_name,
                "web_content": web_content,
                "youtube_content": "",
                "scrapbook_content": "",
            }

    return {
        **state,
        "raw_data": list(existing.values()),
        "errors": errors,
        "current_step": "web_scraping_complete",
    }
