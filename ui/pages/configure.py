import streamlit as st
from db.database import (
    get_all_competitors, add_competitor,
    update_competitor, delete_competitor
)
from agent.tools.gdrive_tool import list_scrapbook_vendors


def render():
    st.header("⚙️ Configure Competitors")
    st.caption("Add and manage the vendors you want to track.")

    # ── Add New Competitor ─────────────────────────────────────────────────────
    with st.expander("➕ Add New Competitor", expanded=False):
        with st.form("add_competitor_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                name = st.text_input("Vendor Name *", placeholder="e.g. Salesforce")
                website = st.text_input("Website URL", placeholder="https://salesforce.com")
            with col2:
                blog = st.text_input("Blog URL", placeholder="https://salesforce.com/blog")
                youtube = st.text_input("YouTube Channel", placeholder="@SalesforceYT or channel ID")

            submitted = st.form_submit_button("Save Competitor", type="primary")
            if submitted:
                if not name.strip():
                    st.error("Vendor name is required.")
                else:
                    success = add_competitor(name.strip(), website, blog, youtube)
                    if success:
                        st.success(f"✅ {name} added successfully.")
                        st.rerun()
                    else:
                        st.error(f"A competitor named '{name}' already exists.")

    st.divider()

    # ── Existing Competitors ───────────────────────────────────────────────────
    competitors = get_all_competitors()

    if not competitors:
        st.info("No competitors configured yet. Add your first one above.")
        return

    st.subheader(f"Saved Competitors ({len(competitors)})")

    # Check which vendors have scrapbook docs in Drive
    try:
        scrapbook_vendors = [v.lower() for v in list_scrapbook_vendors()]
    except Exception:
        scrapbook_vendors = []

    for comp in competitors:
        has_scrapbook = any(
            comp["vendor_name"].lower() in v or v in comp["vendor_name"].lower()
            for v in scrapbook_vendors
        )
        scrapbook_badge = "📄 Scrapbook doc found" if has_scrapbook else "⚠️ No scrapbook doc"

        with st.expander(f"🏢 {comp['vendor_name']}  ·  {scrapbook_badge}", expanded=False):
            with st.form(f"edit_{comp['id']}"):
                col1, col2 = st.columns(2)
                with col1:
                    new_name = st.text_input("Vendor Name", value=comp["vendor_name"])
                    new_website = st.text_input("Website URL", value=comp["website_url"] or "")
                with col2:
                    new_blog = st.text_input("Blog URL", value=comp["blog_url"] or "")
                    new_youtube = st.text_input("YouTube Channel", value=comp["youtube_channel"] or "")

                col_save, col_delete = st.columns([3, 1])
                with col_save:
                    if st.form_submit_button("💾 Save Changes", type="primary"):
                        update_competitor(comp["id"], new_name, new_website, new_blog, new_youtube)
                        st.success("Saved.")
                        st.rerun()
                with col_delete:
                    if st.form_submit_button("🗑️ Delete", type="secondary"):
                        delete_competitor(comp["id"])
                        st.rerun()
