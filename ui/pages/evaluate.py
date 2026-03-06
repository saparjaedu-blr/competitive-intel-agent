import time
import streamlit as st
from db.database import get_all_competitors
from agent.graph import run_agent
from mailer.emailer import send_report_email


# ── Custom CSS — Onyx/deep blue professional theme ────────────────────────────
CUSTOM_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600&family=DM+Mono:wght@400;500&display=swap');

html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
}

/* Main container */
.block-container {
    padding-top: 2rem;
    max-width: 1100px;
}

/* Metric cards for timing */
.timing-card {
    background: linear-gradient(135deg, #111827 0%, #1a2235 100%);
    border: 1px solid #1e3a5f;
    border-radius: 12px;
    padding: 16px 20px;
    margin: 4px 0;
}
.timing-label {
    font-size: 11px;
    font-weight: 600;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: #64748b;
    margin-bottom: 4px;
}
.timing-value {
    font-family: 'DM Mono', monospace;
    font-size: 28px;
    font-weight: 500;
    color: #2B7FFF;
    line-height: 1;
}
.timing-sub {
    font-size: 11px;
    color: #475569;
    margin-top: 4px;
}

/* Drive toggle card */
.drive-option-card {
    background: linear-gradient(135deg, #0f172a 0%, #111827 100%);
    border: 1px solid #1e293b;
    border-radius: 12px;
    padding: 16px 20px;
    margin: 12px 0;
}

/* Section headers */
.section-header {
    font-size: 13px;
    font-weight: 600;
    letter-spacing: 0.06em;
    text-transform: uppercase;
    color: #64748b;
    margin: 24px 0 12px 0;
    padding-bottom: 8px;
    border-bottom: 1px solid #1e293b;
}

/* Vendor expander styling */
.vendor-tag {
    display: inline-block;
    background: #1e3a5f;
    color: #2B7FFF;
    border-radius: 6px;
    padding: 2px 10px;
    font-size: 12px;
    font-weight: 600;
    margin-right: 6px;
}

/* Save indicator pill */
.save-pill {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    background: #0f2a1a;
    border: 1px solid #166534;
    color: #4ade80;
    border-radius: 20px;
    padding: 4px 12px;
    font-size: 12px;
    font-weight: 500;
}
.nosave-pill {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    background: #1a1a0f;
    border: 1px solid #713f12;
    color: #fbbf24;
    border-radius: 20px;
    padding: 4px 12px;
    font-size: 12px;
    font-weight: 500;
}

/* Tab styling */
.stTabs [data-baseweb="tab"] {
    font-size: 12px;
    font-weight: 500;
    letter-spacing: 0.02em;
}

/* Buttons */
.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #1d4ed8, #2B7FFF);
    border: none;
    border-radius: 8px;
    font-weight: 600;
    letter-spacing: 0.02em;
    padding: 10px 24px;
    transition: all 0.2s;
}
.stButton > button[kind="primary"]:hover {
    transform: translateY(-1px);
    box-shadow: 0 4px 20px rgba(43, 127, 255, 0.4);
}

/* Progress bar */
.stProgress > div > div {
    background: linear-gradient(90deg, #1d4ed8, #2B7FFF, #60a5fa);
    border-radius: 4px;
}

/* Info/warning boxes */
.stAlert {
    border-radius: 10px;
    border-left-width: 3px;
}
</style>
"""


def render():
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

    # Page header
    st.markdown("## Intelligence Evaluation")
    st.markdown(
        "<p style='color:#64748b;margin-top:-8px;font-size:14px'>"
        "Configure your research scope and run the AI agent across selected competitors.</p>",
        unsafe_allow_html=True
    )

    competitors = get_all_competitors()
    if not competitors:
        st.warning("No competitors configured yet. Go to **Configure Competitors** to add some.")
        return

    # ── Research Configuration ─────────────────────────────────────────────────
    st.markdown("<div class='section-header'>Research Configuration</div>", unsafe_allow_html=True)

    research_query = st.text_area(
        "Research Focus",
        placeholder="e.g. What AI model capabilities, API features, and pricing models are competitors shipping — and where are the key differentiation points?",
        height=90,
        help="Be specific. This drives the entire synthesis depth and direction.",
        label_visibility="collapsed",
    )

    vendor_names = [c["vendor_name"] for c in competitors]
    selected_vendors = st.multiselect(
        "Vendors to Evaluate",
        options=vendor_names,
        default=vendor_names,
    )

    # ── Drive Save Option ──────────────────────────────────────────────────────
    st.markdown("<div class='section-header'>Report Persistence</div>", unsafe_allow_html=True)

    col_drive, col_info = st.columns([2, 3])
    with col_drive:
        save_to_drive = st.checkbox(
            "📤  Publish & Archive Report",
            value=False,
            help="When enabled: saves to Report History, uploads to Google Drive, and enables the Drive link after completion."
        )
    with col_info:
        if save_to_drive:
            st.markdown(
                "<div class='save-pill'>✦ Report will be archived to History & Google Drive</div>",
                unsafe_allow_html=True
            )
        else:
            st.markdown(
                "<div class='nosave-pill'>⚡ Live analysis only — not saved to History or Drive</div>",
                unsafe_allow_html=True
            )

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Run Button ─────────────────────────────────────────────────────────────
    run_button = st.button(
        "⚡  Run Intelligence Evaluation",
        type="primary",
        disabled=not selected_vendors,
        use_container_width=True,
    )

    if run_button:
        if not research_query.strip():
            st.warning("Please enter a research focus before running.")
            return
        _run_with_progress(selected_vendors, research_query, save_to_drive)

    # ── Display Results ────────────────────────────────────────────────────────
    if "agent_result" in st.session_state:
        _render_results(st.session_state["agent_result"])


def _run_with_progress(selected_vendors, research_query, save_to_drive):
    steps = [
        ("🌐", "Scraping websites and blogs..."),
        ("📚", "Fetching documentation and changelogs..."),
        ("🎬", "Fetching YouTube transcripts..."),
        ("📄", "Reading scrapbook notes and images..."),
        ("🧠", "Synthesizing with GPT-4o..."),
        ("🔄", "Computing delta vs previous run..."),
        ("📝", "Compiling final report..."),
    ]

    progress_bar = st.progress(0)
    status_text = st.empty()

    for i, (icon, label) in enumerate(steps):
        status_text.markdown(
            f"<p style='color:#94a3b8;font-size:13px'>{icon}&nbsp; {label}</p>",
            unsafe_allow_html=True
        )
        progress_bar.progress((i + 1) / len(steps) * 0.85)
        time.sleep(0.35)

    try:
        analysis_start = time.time()
        result = run_agent(selected_vendors, research_query, save_to_drive=save_to_drive)
        analysis_duration = round(time.time() - analysis_start, 1)

        # Inject timing into result
        result["analysis_duration_seconds"] = analysis_duration
        result["save_to_drive"] = save_to_drive

        progress_bar.progress(1.0)
        status_text.markdown(
            "<p style='color:#4ade80;font-size:13px'>✓&nbsp; Evaluation complete</p>",
            unsafe_allow_html=True
        )
        time.sleep(0.6)
        status_text.empty()
        progress_bar.empty()

        st.session_state["agent_result"] = result

    except Exception as e:
        progress_bar.empty()
        status_text.empty()
        st.error(f"Evaluation failed: {str(e)}")


def _render_results(result: dict):
    st.divider()

    # ── Timing Display ─────────────────────────────────────────────────────────
    analysis_secs = result.get("analysis_duration_seconds", 0)
    drive_secs = result.get("drive_duration_seconds", 0)
    save_to_drive = result.get("save_to_drive", False)

    st.markdown("<div class='section-header'>Evaluation Performance</div>", unsafe_allow_html=True)

    if save_to_drive and drive_secs > 0:
        c1, c2, c3 = st.columns(3)
        total = round(analysis_secs + drive_secs, 1)
        with c1:
            st.markdown(f"""
                <div class='timing-card'>
                    <div class='timing-label'>AI Analysis</div>
                    <div class='timing-value'>{analysis_secs}s</div>
                    <div class='timing-sub'>Scraping → Synthesis → Diff</div>
                </div>""", unsafe_allow_html=True)
        with c2:
            st.markdown(f"""
                <div class='timing-card'>
                    <div class='timing-label'>Drive Archive</div>
                    <div class='timing-value'>{drive_secs}s</div>
                    <div class='timing-sub'>Upload + Report History save</div>
                </div>""", unsafe_allow_html=True)
        with c3:
            st.markdown(f"""
                <div class='timing-card'>
                    <div class='timing-label'>Total Duration</div>
                    <div class='timing-value'>{total}s</div>
                    <div class='timing-sub'>{len(result.get("syntheses", []))} vendor(s) analyzed</div>
                </div>""", unsafe_allow_html=True)
    else:
        c1, c2 = st.columns(2)
        with c1:
            st.markdown(f"""
                <div class='timing-card'>
                    <div class='timing-label'>AI Analysis Duration</div>
                    <div class='timing-value'>{analysis_secs}s</div>
                    <div class='timing-sub'>Scraping → Synthesis → Diff</div>
                </div>""", unsafe_allow_html=True)
        with c2:
            vendor_count = len(result.get("syntheses", []))
            per_vendor = round(analysis_secs / vendor_count, 1) if vendor_count else 0
            st.markdown(f"""
                <div class='timing-card'>
                    <div class='timing-label'>Avg. Per Vendor</div>
                    <div class='timing-value'>{per_vendor}s</div>
                    <div class='timing-sub'>{vendor_count} vendor(s) analyzed</div>
                </div>""", unsafe_allow_html=True)

    # ── Warnings ────────────────────────────────────────────────────────────
    if result.get("errors"):
        with st.expander("⚠️ Run Warnings", expanded=False):
            for err in result["errors"]:
                st.caption(err)

    # ── What's New (Delta) ──────────────────────────────────────────────────
    diffs = result.get("diffs", [])
    if diffs:
        st.markdown("<div class='section-header'>Delta — What's New Since Last Run</div>", unsafe_allow_html=True)
        for diff in diffs:
            with st.expander(f"  {diff['vendor_name']}", expanded=True):
                if diff.get("is_first_run"):
                    st.info(diff["delta_summary"])
                else:
                    st.markdown(diff["delta_summary"])

    # ── Per-Vendor Analysis ─────────────────────────────────────────────────
    st.markdown("<div class='section-header'>Full Intelligence Report</div>", unsafe_allow_html=True)
    syntheses = result.get("syntheses", [])
    for synthesis in syntheses:
        with st.expander(f"  {synthesis['vendor_name']}", expanded=False):
            tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8 = st.tabs([
                "🚀 Launches",
                "🎯 Use Cases",
                "⚙️ Technical",
                "🖥️ UI/UX",
                "💰 Pricing",
                "🧭 Direction",
                "⚔️ Gaps",
                "👁️ Watch",
            ])
            with tab1:
                st.markdown(synthesis.get("recent_launches", "_No data retrieved_"))
            with tab2:
                st.markdown(synthesis.get("use_cases", "_No data retrieved_"))
            with tab3:
                st.markdown(synthesis.get("technical_details", "_No data retrieved_"))
            with tab4:
                st.markdown(synthesis.get("ui_ux", "_No data retrieved_"))
            with tab5:
                st.markdown(synthesis.get("pricing_signals", "_No data retrieved_"))
            with tab6:
                st.markdown(synthesis.get("strategic_direction", "_No data retrieved_"))
            with tab7:
                st.markdown(synthesis.get("gap_vs_your_product", "_No data retrieved_"))
            with tab8:
                st.markdown(synthesis.get("watch_points", "_No data retrieved_"))

    # ── Action Bar ──────────────────────────────────────────────────────────
    st.divider()
    col1, col2, col3 = st.columns([2, 2, 1])

    with col1:
        gdrive_link = result.get("gdrive_link", "")
        if gdrive_link and not gdrive_link.startswith("[") and gdrive_link != "__local_only__":
            st.link_button("📁  Open in Google Drive", gdrive_link, type="secondary", use_container_width=True)
        else:
            if not save_to_drive:
                st.button(
                    "📁  Google Drive",
                    disabled=True,
                    help="Enable 'Publish & Archive Report' to upload to Drive",
                    use_container_width=True
                )

    with col2:
        if st.button("📧  Distribute via Email", type="primary", use_container_width=True):
            st.session_state["show_email_modal"] = True

    if st.session_state.get("show_email_modal"):
        _render_email_modal(result)


def _render_email_modal(result: dict):
    st.markdown("---")
    with st.form("email_form"):
        st.markdown("#### 📧 Distribute Report")
        st.caption("Enter one email address per line.")
        emails_raw = st.text_area(
            "Recipients",
            placeholder="alice@company.com\nbob@company.com",
            height=100,
            label_visibility="collapsed",
        )
        col_send, col_cancel = st.columns(2)
        with col_send:
            send = st.form_submit_button("Send Report", type="primary", use_container_width=True)
        with col_cancel:
            cancel = st.form_submit_button("Cancel", use_container_width=True)

        if cancel:
            st.session_state["show_email_modal"] = False
            st.rerun()

        if send:
            recipients = [e.strip() for e in emails_raw.splitlines() if e.strip()]
            if not recipients:
                st.error("Please enter at least one email address.")
            else:
                with st.spinner("Sending..."):
                    outcome = send_report_email(
                        recipients=recipients,
                        report_markdown=result.get("final_report_markdown", ""),
                        gdrive_link=result.get("gdrive_link", ""),
                    )
                if outcome["success"]:
                    st.success(f"✅ Report distributed to {len(recipients)} recipient(s).")
                    st.session_state["show_email_modal"] = False
                else:
                    st.error(f"Send failed: {outcome['error']}")
