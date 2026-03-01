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
                docs = st.text_input("Docs URL", placeholder="https://developer.salesforce.com/docs")
            with col2:
                blog = st.text_input("Blog URL", placeholder="https://salesforce.com/blog")
                changelog = st.text_input("Changelog / Release Notes URL", placeholder="https://salesforce.com/releases")
                youtube = st.text_input("YouTube Channel", placeholder="@SalesforceYT or channel ID")

            st.caption("💡 Docs and Changelog URLs unlock technical depth — protocols, APIs, release history.")

            submitted = st.form_submit_button("Save Competitor", type="primary")
            if submitted:
                if not name.strip():
                    st.error("Vendor name is required.")
                else:
                    success = add_competitor(
                        name.strip(), website, blog, docs, changelog, youtube
                    )
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

    try:
        scrapbook_vendors = [v.lower() for v in list_scrapbook_vendors()]
    except Exception:
        scrapbook_vendors = []

    for comp in competitors:
        has_scrapbook = any(
            comp["vendor_name"].lower() in v or v in comp["vendor_name"].lower()
            for v in scrapbook_vendors
        )
        has_docs = bool(comp.get("docs_url") or comp.get("changelog_url"))
        badges = []
        if has_scrapbook:
            badges.append("📄 Scrapbook")
        if has_docs:
            badges.append("📚 Docs/Changelog")
        badge_str = "  ·  " + "  ".join(badges) if badges else ""

        with st.expander(f"🏢 {comp['vendor_name']}{badge_str}", expanded=False):
            with st.form(f"edit_{comp['id']}"):
                col1, col2 = st.columns(2)
                with col1:
                    new_name = st.text_input("Vendor Name", value=comp["vendor_name"])
                    new_website = st.text_input("Website URL", value=comp.get("website_url") or "")
                    new_docs = st.text_input("Docs URL", value=comp.get("docs_url") or "")
                with col2:
                    new_blog = st.text_input("Blog URL", value=comp.get("blog_url") or "")
                    new_changelog = st.text_input("Changelog URL", value=comp.get("changelog_url") or "")
                    new_youtube = st.text_input("YouTube Channel", value=comp.get("youtube_channel") or "")

                col_save, col_delete = st.columns([3, 1])
                with col_save:
                    if st.form_submit_button("💾 Save Changes", type="primary"):
                        update_competitor(
                            comp["id"], new_name, new_website, new_blog,
                            new_docs, new_changelog, new_youtube
                        )
                        st.success("Saved.")
                        st.rerun()
                with col_delete:
                    if st.form_submit_button("🗑️ Delete", type="secondary"):
                        delete_competitor(comp["id"])
                        st.rerun()
