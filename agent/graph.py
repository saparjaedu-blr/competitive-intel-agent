from langgraph.graph import StateGraph, END
from agent.state import AgentState
from agent.nodes.web_scraper import web_scraper_node
from agent.nodes.youtube_scraper import youtube_scraper_node
from agent.nodes.gdoc_reader import gdoc_reader_node
from agent.nodes.synthesizer import synthesizer_node
from agent.nodes.diff_engine import diff_engine_node
from agent.nodes.report_writer import report_writer_node


def build_graph() -> StateGraph:
    """
    Build and compile the competitive intelligence LangGraph.

    Flow:
        web_scraper → youtube_scraper → gdoc_reader
                                              ↓
                                        synthesizer
                                              ↓
                                        diff_engine
                                              ↓
                                        report_writer → END
    """
    graph = StateGraph(AgentState)

    # ── Register nodes ─────────────────────────────────────────────────────────
    graph.add_node("web_scraper", web_scraper_node)
    graph.add_node("youtube_scraper", youtube_scraper_node)
    graph.add_node("gdoc_reader", gdoc_reader_node)
    graph.add_node("synthesizer", synthesizer_node)
    graph.add_node("diff_engine", diff_engine_node)
    graph.add_node("report_writer", report_writer_node)

    # ── Define edges ───────────────────────────────────────────────────────────
    graph.set_entry_point("web_scraper")
    graph.add_edge("web_scraper", "youtube_scraper")
    graph.add_edge("youtube_scraper", "gdoc_reader")
    graph.add_edge("gdoc_reader", "synthesizer")
    graph.add_edge("synthesizer", "diff_engine")
    graph.add_edge("diff_engine", "report_writer")
    graph.add_edge("report_writer", END)

    return graph.compile()


def run_agent(vendors: list[str], research_query: str) -> AgentState:
    """
    Entry point to run the full agent pipeline.
    
    Args:
        vendors: List of vendor names to analyze (must exist in DB)
        research_query: The PM's research focus, e.g. "What AI features are competitors shipping?"
    
    Returns:
        Final AgentState with report_markdown and gdrive_link populated.
    """
    app = build_graph()

    initial_state: AgentState = {
        "vendors": vendors,
        "research_query": research_query,
        "raw_data": [],
        "syntheses": [],
        "diffs": [],
        "final_report_markdown": "",
        "gdrive_link": "",
        "errors": [],
        "current_step": "starting",
    }

    final_state = app.invoke(initial_state)
    return final_state
