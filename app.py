import streamlit as st
from db.database import init_db
from ui.pages import configure, evaluate, history

# ── Page Config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Competitive Intelligence Agent",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Init DB on first run ───────────────────────────────────────────────────────
init_db()

# ── Sidebar Navigation ─────────────────────────────────────────────────────────
with st.sidebar:
    st.title("🔍 CompIntel Agent")
    st.caption("AI-powered competitive intelligence for Product Managers")
    st.divider()

    page = st.radio(
        "Navigation",
        options=["Evaluate Competitors", "Configure Competitors", "Report History"],
        index=0,
    )

    st.divider()
    st.caption("Built with LangGraph + GPT-4o")

# ── Render Page ────────────────────────────────────────────────────────────────
if page == "Configure Competitors":
    configure.render()
elif page == "Evaluate Competitors":
    evaluate.render()
elif page == "Report History":
    history.render()
