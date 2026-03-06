from langgraph.graph import StateGraph, END
from agent.state import AgentState
from agent.nodes.web_scraper import web_scraper_node
from agent.nodes.youtube_scraper import youtube_scraper_node
from agent.nodes.gdoc_reader import gdoc_reader_node
from agent.nodes.synthesizer import synthesizer_node
from agent.nodes.diff_engine import diff_engine_node
from agent.nodes.report_writer import report_writer_node


def build_graph() -> StateGraph:
    graph = StateGraph(AgentState)
    graph.add_node("web_scraper", web_scraper_node)
    graph.add_node("youtube_scraper", youtube_scraper_node)
    graph.add_node("gdoc_reader", gdoc_reader_node)
    graph.add_node("synthesizer", synthesizer_node)
    graph.add_node("diff_engine", diff_engine_node)
    graph.add_node("report_writer", report_writer_node)

    graph.set_entry_point("web_scraper")
    graph.add_edge("web_scraper", "youtube_scraper")
    graph.add_edge("youtube_scraper", "gdoc_reader")
    graph.add_edge("gdoc_reader", "synthesizer")
    graph.add_edge("synthesizer", "diff_engine")
    graph.add_edge("diff_engine", "report_writer")
    graph.add_edge("report_writer", END)

    return graph.compile()


def run_agent(vendors: list[str], research_query: str, save_to_drive: bool = False) -> AgentState:
    """
    Entry point to run the full agent pipeline.

    Args:
        vendors: List of vendor names to analyze (must exist in DB)
        research_query: The PM's research focus
        save_to_drive: Whether to upload report to Google Drive and save to report history
    """
    app = build_graph()

    initial_state: AgentState = {
        "vendors": vendors,
        "research_query": research_query,
        "save_to_drive": save_to_drive,
        "raw_data": [],
        "syntheses": [],
        "diffs": [],
        "final_report_markdown": "",
        "gdrive_link": "",
        "analysis_duration_seconds": 0.0,
        "drive_duration_seconds": 0.0,
        "errors": [],
        "current_step": "starting",
    }

    final_state = app.invoke(initial_state)
    return final_state
