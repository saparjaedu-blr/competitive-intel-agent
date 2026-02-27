import streamlit as st
import json
from db.database import get_all_reports, get_report_by_id


def render():
    st.header("📋 Report History")
    st.caption("All past competitive intelligence reports.")

    reports = get_all_reports()

    if not reports:
        st.info("No reports yet. Run your first evaluation from the **Evaluate Competitors** page.")
        return

    # ── Report List ────────────────────────────────────────────────────────────
    for report in reports:
        vendors = json.loads(report.get("vendors_covered") or "[]")
        vendor_str = ", ".join(vendors) if vendors else "Unknown"

        with st.expander(
            f"📅 {report['run_date']}  ·  {report['research_query'][:60]}",
            expanded=False,
        ):
            col1, col2 = st.columns([3, 1])
            with col1:
                st.caption(f"**Vendors:** {vendor_str}")
                if report.get("gdrive_link") and not report["gdrive_link"].startswith("["):
                    st.link_button("📁 Open in Google Drive", report["gdrive_link"])
            with col2:
                if st.button("📄 View Report", key=f"view_{report['id']}"):
                    st.session_state["viewing_report_id"] = report["id"]

    # ── Report Viewer ──────────────────────────────────────────────────────────
    if "viewing_report_id" in st.session_state:
        report_id = st.session_state["viewing_report_id"]
        report = get_report_by_id(report_id)
        if report:
            st.divider()
            st.subheader(f"Report: {report['run_date']}")
            st.markdown(report["report_markdown"])
            if st.button("✖ Close"):
                del st.session_state["viewing_report_id"]
                st.rerun()
