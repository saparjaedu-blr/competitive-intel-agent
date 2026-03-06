import streamlit as st
from db.database import init_db
from ui.pages import configure, evaluate, history

st.set_page_config(
    page_title="CompIntel — Competitive Intelligence Agent",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

init_db()

# ── Global CSS ─────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600&family=DM+Mono:wght@400;500&display=swap');

html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
}

/* Sidebar */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #080d18 0%, #0a0e1a 100%);
    border-right: 1px solid #1e293b;
}
[data-testid="stSidebar"] .stRadio label {
    font-size: 13px;
    font-weight: 500;
    color: #94a3b8;
    padding: 6px 0;
    letter-spacing: 0.02em;
}
[data-testid="stSidebar"] .stRadio [data-baseweb="radio"] input:checked + div {
    background: #2B7FFF;
}

/* Main background */
.stApp {
    background: #0A0E1A;
}

/* Dividers */
hr {
    border-color: #1e293b !important;
}

/* Expanders */
.streamlit-expanderHeader {
    background: #111827 !important;
    border: 1px solid #1e293b !important;
    border-radius: 10px !important;
    font-weight: 500 !important;
    font-size: 14px !important;
}

/* Input fields */
.stTextInput input, .stTextArea textarea {
    background: #111827 !important;
    border: 1px solid #1e293b !important;
    border-radius: 8px !important;
    color: #e2e8f0 !important;
    font-family: 'DM Sans', sans-serif !important;
}
.stTextInput input:focus, .stTextArea textarea:focus {
    border-color: #2B7FFF !important;
    box-shadow: 0 0 0 2px rgba(43,127,255,0.15) !important;
}

/* Multiselect */
.stMultiSelect [data-baseweb="select"] {
    background: #111827 !important;
    border: 1px solid #1e293b !important;
    border-radius: 8px !important;
}

/* Tabs */
.stTabs [data-baseweb="tab-list"] {
    background: #111827;
    border-radius: 10px;
    padding: 4px;
    gap: 2px;
}
.stTabs [data-baseweb="tab"] {
    border-radius: 7px;
    font-size: 12px;
    font-weight: 500;
    color: #64748b;
}
.stTabs [aria-selected="true"] {
    background: #1e3a5f !important;
    color: #2B7FFF !important;
}

/* Scrollbar */
::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: #0A0E1A; }
::-webkit-scrollbar-thumb { background: #1e293b; border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: #2B7FFF; }
</style>
""", unsafe_allow_html=True)

# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
        <div style='padding: 8px 0 20px 0'>
            <div style='font-size:20px;font-weight:700;color:#e2e8f0;letter-spacing:-0.02em'>
                ⚡ CompIntel
            </div>
            <div style='font-size:11px;color:#475569;margin-top:3px;letter-spacing:0.05em;text-transform:uppercase'>
                AI Competitive Intelligence
            </div>
        </div>
    """, unsafe_allow_html=True)

    st.divider()

    page = st.radio(
        "Navigation",
        options=["Evaluate Competitors", "Configure Competitors", "Report History"],
        index=0,
        label_visibility="collapsed",
    )

    st.divider()

    st.markdown("""
        <div style='font-size:11px;color:#334155;line-height:1.8'>
            <div>Powered by</div>
            <div style='color:#475569'>LangGraph · GPT-4o · Streamlit</div>
        </div>
    """, unsafe_allow_html=True)

# ── Page Routing ───────────────────────────────────────────────────────────────
if page == "Configure Competitors":
    configure.render()
elif page == "Evaluate Competitors":
    evaluate.render()
elif page == "Report History":
    history.render()
