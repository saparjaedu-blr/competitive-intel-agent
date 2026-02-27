from datetime import datetime
from agent.state import AgentState
from agent.tools.gdrive_tool import upload_report_to_drive
from db.database import save_report, save_diff_log


def report_writer_node(state: AgentState) -> AgentState:
    """
    Format the final markdown report, save to SQLite, upload to Google Drive.
    """
    syntheses = state.get("syntheses", [])
    diffs = state.get("diffs", [])
    research_query = state.get("research_query", "General competitive overview")
    vendors = state.get("vendors", [])
    errors = state.get("errors", [])

    # Build diff lookup
    diff_lookup = {d["vendor_name"]: d for d in diffs}

    now = datetime.now()
    date_str = now.strftime("%B %d, %Y")
    time_str = now.strftime("%H:%M")

    # ── Build Markdown Report ──────────────────────────────────────────────────
    lines = [
        f"# Competitive Intelligence Report",
        f"**Date:** {date_str} at {time_str}  ",
        f"**Research Focus:** {research_query}  ",
        f"**Vendors Analyzed:** {', '.join(vendors)}",
        "",
        "---",
        "",
    ]

    # Delta summary section (the most important part — what's new)
    has_changes = any(
        not d.get("is_first_run") and "No significant changes" not in d.get("delta_summary", "")
        for d in diffs
    )

    lines.append("## 🔔 What's New Since Last Run")
    lines.append("")
    if diffs:
        for diff in diffs:
            lines.append(f"### {diff['vendor_name']}")
            lines.append(diff["delta_summary"])
            lines.append("")
    else:
        lines.append("_This is the first run. No previous snapshot to compare against._")
        lines.append("")

    lines.append("---")
    lines.append("")
    lines.append("## 📊 Full Intelligence by Vendor")
    lines.append("")

    for synthesis in syntheses:
        vendor = synthesis["vendor_name"]
        lines += [
            f"## {vendor}",
            "",
            "### Recent Feature Launches & Updates",
            synthesis.get("recent_launches", "_No data_"),
            "",
            "### Pricing Signals",
            synthesis.get("pricing_signals", "_No data_"),
            "",
            "### Strategic Direction",
            synthesis.get("strategic_direction", "_No data_"),
            "",
            "### Gaps vs Your Product",
            synthesis.get("gap_vs_your_product", "_No data_"),
            "",
            "---",
            "",
        ]

    if errors:
        lines += [
            "## ⚠️ Errors During This Run",
            "",
        ]
        for err in errors:
            lines.append(f"- {err}")

    report_markdown = "\n".join(lines)

    # ── Save to SQLite ─────────────────────────────────────────────────────────
    report_id = save_report(
        research_query=research_query,
        vendors_covered=vendors,
        report_markdown=report_markdown,
        gdrive_link="",  # update after upload
    )

    # Save diff logs (used for future diff comparisons)
    for synthesis in syntheses:
        vendor_name = synthesis["vendor_name"]
        diff = diff_lookup.get(vendor_name, {})
        save_diff_log(
            report_id=report_id,
            vendor_name=vendor_name,
            previous_snapshot=diff.get("delta_summary", ""),
            new_snapshot=synthesis["raw_synthesis"],
            delta_summary=diff.get("delta_summary", ""),
        )

    # ── Upload to Google Drive ─────────────────────────────────────────────────
    date_file = now.strftime("%Y-%m-%d")
    filename = f"Competitive Intelligence — {date_file} — {research_query[:40]}"
    gdrive_link = upload_report_to_drive(report_markdown, filename)

    return {
        **state,
        "final_report_markdown": report_markdown,
        "gdrive_link": gdrive_link,
        "errors": errors,
        "current_step": "report_complete",
    }
