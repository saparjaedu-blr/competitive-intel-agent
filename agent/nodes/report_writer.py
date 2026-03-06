import time
from datetime import datetime
from agent.state import AgentState
from agent.tools.gdrive_tool import upload_report_to_drive
from db.database import save_report, save_diff_log


def report_writer_node(state: AgentState) -> AgentState:
    """
    Format the final markdown report.
    Conditionally saves to SQLite + uploads to Google Drive based on save_to_drive flag.
    Tracks timing for analysis and drive upload separately.
    """
    syntheses = state.get("syntheses", [])
    diffs = state.get("diffs", [])
    research_query = state.get("research_query", "General competitive overview")
    vendors = state.get("vendors", [])
    errors = state.get("errors", [])
    save_to_drive = state.get("save_to_drive", False)

    diff_lookup = {d["vendor_name"]: d for d in diffs}

    now = datetime.now()
    date_str = now.strftime("%B %d, %Y")
    time_str = now.strftime("%H:%M")

    # ── Build Markdown Report ──────────────────────────────────────────────────
    lines = [
        "# Competitive Intelligence Report",
        f"**Date:** {date_str} at {time_str}  ",
        f"**Research Focus:** {research_query}  ",
        f"**Vendors Analyzed:** {', '.join(vendors)}",
        "",
        "---",
        "",
        "## 🔔 What's New Since Last Run",
        "",
    ]

    if diffs:
        for diff in diffs:
            lines.append(f"### {diff['vendor_name']}")
            lines.append(diff["delta_summary"])
            lines.append("")
    else:
        lines.append("_This is the first run. No previous snapshot to compare against._")
        lines.append("")

    lines += ["---", "", "## 📊 Full Intelligence by Vendor", ""]

    for synthesis in syntheses:
        vendor = synthesis["vendor_name"]
        lines += [
            f"## {vendor}",
            "",
            "### 🚀 Recent Feature Launches & Updates",
            synthesis.get("recent_launches", "_No data_"),
            "",
            "### 🎯 Use Cases & Target Segments",
            synthesis.get("use_cases", "_No data_"),
            "",
            "### ⚙️ Technical Architecture & Protocol Support",
            synthesis.get("technical_details", "_No data_"),
            "",
            "### 🖥️ User Interface & UX",
            synthesis.get("ui_ux", "_No data_"),
            "",
            "### 💰 Pricing & Packaging",
            synthesis.get("pricing_signals", "_No data_"),
            "",
            "### 🧭 Strategic Direction",
            synthesis.get("strategic_direction", "_No data_"),
            "",
            "### ⚔️ Gaps vs Your Product",
            synthesis.get("gap_vs_your_product", "_No data_"),
            "",
            "### 👁️ Key Watch Points",
            synthesis.get("watch_points", "_No data_"),
            "",
            "---",
            "",
        ]

    if errors:
        lines += ["## ⚠️ Errors During This Run", ""]
        for err in errors:
            lines.append(f"- {err}")

    report_markdown = "\n".join(lines)

    # ── Save to SQLite + Drive (only if save_to_drive is enabled) ─────────────
    gdrive_link = ""
    drive_duration = 0.0

    if save_to_drive:
        drive_start = time.time()

        report_id = save_report(
            research_query=research_query,
            vendors_covered=vendors,
            report_markdown=report_markdown,
            gdrive_link="",
        )

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

        date_file = now.strftime("%Y-%m-%d")
        filename = f"Competitive Intelligence — {date_file} — {research_query[:40]}"
        gdrive_link = upload_report_to_drive(report_markdown, filename)

        drive_duration = round(time.time() - drive_start, 1)
    else:
        # Still save diff logs to SQLite for future diff comparisons
        # but do NOT save the full report or upload to Drive
        report_id = save_report(
            research_query=research_query,
            vendors_covered=vendors,
            report_markdown=report_markdown,
            gdrive_link="__local_only__",
        )
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

    return {
        **state,
        "final_report_markdown": report_markdown,
        "gdrive_link": gdrive_link,
        "drive_duration_seconds": drive_duration,
        "errors": errors,
        "current_step": "report_complete",
    }
