from agent.state import AgentState
from agent.tools.gdrive_tool import get_scrapbook_section


def gdoc_reader_node(state: AgentState) -> AgentState:
    """
    Read personal scrapbook notes and images from Google Doc for each vendor.
    The scrapbook folder contains one Doc per competitor, named after the vendor.
    Each Doc can have multiple tabs grouping features by category.
    Updates scrapbook_content and scrapbook_images in raw_data.
    """
    vendors = state["vendors"]
    raw_data = {d["vendor_name"]: d for d in state.get("raw_data", [])}
    errors = state.get("errors", [])

    for vendor_name in vendors:
        result = get_scrapbook_section(vendor_name)
        scrapbook_text = result.get("text", "")
        scrapbook_images = result.get("images", [])

        if vendor_name in raw_data:
            raw_data[vendor_name]["scrapbook_content"] = scrapbook_text
            raw_data[vendor_name]["scrapbook_images"] = scrapbook_images
        else:
            raw_data[vendor_name] = {
                "vendor_name": vendor_name,
                "web_content": "",
                "youtube_content": "",
                "scrapbook_content": scrapbook_text,
                "scrapbook_images": scrapbook_images,
            }

        if scrapbook_images:
            img_count = len(scrapbook_images)
            errors_msg = f"📸 {img_count} image(s) found in scrapbook for {vendor_name} — will be analyzed by GPT-4o"
            # Use errors list as a general log here (not actually an error)
            # In a future version this could be a proper log channel

    return {
        **state,
        "raw_data": list(raw_data.values()),
        "errors": errors,
        "current_step": "gdoc_reading_complete",
    }
