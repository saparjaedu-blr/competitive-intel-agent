import streamlit as st
import json
from db.database import get_all_reports, get_report_by_id


def _is_valid_drive_link(link: str) -> bool:
    """Return True only if this is a real, usable Google Drive URL."""
    if not link:
        return False
    if link.startswith("["):        # placeholder like "[Drive upload failed]"
        return False
    if link == "__local_only__":    # saved without Drive option
        return False
    if not link.startswith("http"): # any other non-URL value
        return False
    return True


def render():
    st.markdown("## Report History")
    st.markdown(
        "<p style='color:#64748b;margin-top:-8px;font-size:14px'>"
        "All archived competitive intelligence reports.</p>",
        unsafe_allow_html=True
    )

    reports = get_all_reports()

    # Filter out local-only reports (not published to Drive / history)
    published = [r for r in reports if r.get("gdrive_link") != "__local_only__"
                 or r.get("report_markdown")]

    if not published:
        st.info("No archived reports yet. Run an evaluation with **Publish & Archive Report** enabled.")
        return

    # ── Report List ────────────────────────────────────────────────────────────
    for report in published:
        vendors = json.loads(report.get("vendors_covered") or "[]")
        vendor_str = ", ".join(vendors) if vendors else "—"
        gdrive_link = report.get("gdrive_link", "")
        has_drive = _is_valid_drive_link(gdrive_link)

        label = f"📅  {report['run_date']}  ·  {(report['research_query'] or '')[:65]}"

        with st.expander(label, expanded=False):
            col_meta, col_actions = st.columns([3, 2])

            with col_meta:
                st.markdown(
                    f"<p style='font-size:12px;color:#64748b;margin:0'>"
                    f"<b style='color:#475569'>Vendors:</b> {vendor_str}</p>",
                    unsafe_allow_html=True
                )
                if has_drive:
                    st.markdown(
                        "<span style='display:inline-flex;align-items:center;gap:4px;"
                        "background:#eff6ff;border:1px solid #bfdbfe;border-radius:12px;"
                        "padding:2px 10px;font-size:11px;font-weight:600;color:#1d4ed8;"
                        "margin-top:6px'>☁ Archived to Google Drive</span>",
                        unsafe_allow_html=True
                    )
                else:
                    st.markdown(
                        "<span style='display:inline-flex;align-items:center;gap:4px;"
                        "background:#f8f7f4;border:1px solid #e8e4dd;border-radius:12px;"
                        "padding:2px 10px;font-size:11px;font-weight:500;color:#94a3b8;"
                        "margin-top:6px'>Local only</span>",
                        unsafe_allow_html=True
                    )

            with col_actions:
                btn_col1, btn_col2 = st.columns(2)
                with btn_col1:
                    if has_drive:
                        st.link_button(
                            "☁ Open in Drive",
                            gdrive_link,
                            use_container_width=True,
                        )
                    else:
                        st.button(
                            "☁ Google Drive",
                            disabled=True,
                            key=f"drive_disabled_{report['id']}",
                            help="This report was not published to Google Drive",
                            use_container_width=True,
                        )
                with btn_col2:
                    if st.button(
                        "📄 View Report",
                        key=f"view_{report['id']}",
                        use_container_width=True,
                    ):
                        st.session_state["viewing_report_id"] = report["id"]

    # ── Inline Report Viewer ───────────────────────────────────────────────────
    if "viewing_report_id" in st.session_state:
        report_id = st.session_state["viewing_report_id"]
        report = get_report_by_id(report_id)
        if report:
            st.divider()
            st.markdown(
                f"<p style='font-size:11px;font-weight:700;letter-spacing:0.07em;"
                f"text-transform:uppercase;color:#94a3b8'>Viewing Report</p>"
                f"<h3 style='margin-top:4px;color:#0f172a'>{report['run_date']}</h3>",
                unsafe_allow_html=True
            )
            st.markdown(report["report_markdown"])
            st.divider()
            if st.button("✕  Close Report", type="secondary"):
                del st.session_state["viewing_report_id"]
                st.rerun()
