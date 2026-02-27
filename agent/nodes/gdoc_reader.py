from agent.state import AgentState
from agent.tools.gdrive_tool import get_scrapbook_section


def gdoc_reader_node(state: AgentState) -> AgentState:
    """
    Read personal scrapbook notes from Google Doc for each vendor.
    The Doc must have Heading 1/2 sections named after each vendor.
    Updates scrapbook_content in raw_data.
    """
    vendors = state["vendors"]
    raw_data = {d["vendor_name"]: d for d in state.get("raw_data", [])}
    errors = state.get("errors", [])

    for vendor_name in vendors:
        scrapbook_content = get_scrapbook_section(vendor_name)

        if vendor_name in raw_data:
            raw_data[vendor_name]["scrapbook_content"] = scrapbook_content
        else:
            raw_data[vendor_name] = {
                "vendor_name": vendor_name,
                "web_content": "",
                "youtube_content": "",
                "scrapbook_content": scrapbook_content,
            }

    return {
        **state,
        "raw_data": list(raw_data.values()),
        "errors": errors,
        "current_step": "gdoc_reading_complete",
    }
