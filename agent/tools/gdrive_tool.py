import os
import io
from datetime import datetime
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
from config.settings import GOOGLE_SCOPES, GOOGLE_DRIVE_FOLDER_ID, GOOGLE_DOC_SCRAPBOOK_ID

TOKEN_PATH = "token.json"
CREDENTIALS_PATH = "credentials.json"


def get_google_creds() -> Credentials:
    """Get or refresh Google OAuth credentials."""
    creds = None

    if os.path.exists(TOKEN_PATH):
        creds = Credentials.from_authorized_user_file(TOKEN_PATH, GOOGLE_SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_PATH, GOOGLE_SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN_PATH, "w") as token_file:
            token_file.write(creds.to_json())

    return creds


# ── Google Doc Reader (Folder-based, multi-tab) ────────────────────────────────

def list_docs_in_scrapbook_folder(folder_id: str = None) -> list[dict]:
    """
    List all Google Docs inside the Competitor Scrapbook folder.
    Returns: [{"doc_id": "...", "name": "Salesforce"}, ...]
    
    Doc filename in Drive = competitor name (e.g. "Salesforce", "HubSpot")
    """
    folder_id = folder_id or GOOGLE_DOC_SCRAPBOOK_ID
    if not folder_id:
        return []

    try:
        creds = get_google_creds()
        drive_service = build("drive", "v3", credentials=creds)

        query = (
            f"'{folder_id}' in parents "
            f"and mimeType='application/vnd.google-apps.document' "
            f"and trashed=false"
        )

        results = drive_service.files().list(
            q=query,
            fields="files(id, name)",
            orderBy="name",
        ).execute()

        return [
            {"doc_id": f["id"], "name": f["name"]}
            for f in results.get("files", [])
        ]

    except Exception as e:
        return []


def _extract_text_from_body(content: list) -> str:
    """Extract clean text from a Google Doc body content array."""
    lines = []
    for element in content:
        paragraph = element.get("paragraph")
        if not paragraph:
            continue
        text_runs = paragraph.get("elements", [])
        text = "".join(
            r.get("textRun", {}).get("content", "") for r in text_runs
        ).strip()
        if text:
            # Preserve heading context as bold markers
            style = paragraph.get("paragraphStyle", {}).get("namedStyleType", "")
            if style in ("HEADING_1", "HEADING_2", "HEADING_3"):
                lines.append(f"\n## {text}")
            else:
                lines.append(text)
    return "\n".join(lines)


def read_competitor_doc(doc_id: str) -> str:
    """
    Read a single competitor Google Doc, including all tabs if present.
    Each tab is treated as a feature category group.
    
    Returns: Full text content with tab names as section headers.
    """
    try:
        creds = get_google_creds()
        docs_service = build("docs", "v1", credentials=creds)

        # Fetch doc with tabs included
        doc = docs_service.documents().get(
            documentId=doc_id,
            includeTabsContent=True,
        ).execute()

        all_text_parts = []

        # ── Multi-tab doc ──────────────────────────────────────────────────────
        tabs = doc.get("tabs", [])
        if tabs:
            for tab in tabs:
                tab_props = tab.get("tabProperties", {})
                tab_title = tab_props.get("title", "Notes")

                # Nested tabs (sub-tabs) — flatten them too
                child_tabs = tab.get("childTabs", [])
                tabs_to_read = [tab] + child_tabs

                for t in tabs_to_read:
                    doc_tab = t.get("documentTab", {})
                    body_content = doc_tab.get("body", {}).get("content", [])
                    if body_content:
                        tab_text = _extract_text_from_body(body_content)
                        if tab_text.strip():
                            child_title = t.get("tabProperties", {}).get("title", tab_title)
                            all_text_parts.append(f"\n### Tab: {child_title}\n{tab_text}")

        # ── Single-tab / no tabs fallback ──────────────────────────────────────
        if not all_text_parts:
            body_content = doc.get("body", {}).get("content", [])
            fallback_text = _extract_text_from_body(body_content)
            if fallback_text.strip():
                all_text_parts.append(fallback_text)

        return "\n\n".join(all_text_parts)

    except Exception as e:
        return f"[Could not read doc {doc_id}: {str(e)}]"


def get_scrapbook_section(vendor_name: str) -> str:
    """
    Find and read the Google Doc for a specific vendor from the scrapbook folder.
    Matches doc filename to vendor name (case-insensitive, partial match).
    Reads all tabs within the doc.
    
    Folder structure expected:
        📁 Competitor Scrapbook/
            📄 Salesforce          ← filename matches vendor name
            📄 HubSpot
            📄 Zoho CRM
    
    Each doc can have multiple tabs grouping features by category.
    """
    docs = list_docs_in_scrapbook_folder()
    if not docs:
        return ""

    vendor_lower = vendor_name.lower()

    # Find the doc whose filename matches the vendor name
    matched_doc = None
    for doc in docs:
        if vendor_lower in doc["name"].lower() or doc["name"].lower() in vendor_lower:
            matched_doc = doc
            break

    if not matched_doc:
        return ""

    content = read_competitor_doc(matched_doc["doc_id"])
    return f"=== Scrapbook: {matched_doc['name']} ===\n{content}"


def list_scrapbook_vendors() -> list[str]:
    """
    Return all vendor names found in the scrapbook folder.
    Useful for the UI to show which vendors have scrapbook docs.
    """
    docs = list_docs_in_scrapbook_folder()
    return [d["name"] for d in docs]


# ── Google Drive Writer ────────────────────────────────────────────────────────

def upload_report_to_drive(report_markdown: str, filename: str = None) -> str:
    """
    Upload a markdown report to Google Drive as a Google Doc.
    Returns the shareable link.
    """
    if not GOOGLE_DRIVE_FOLDER_ID:
        return ""

    try:
        creds = get_google_creds()
        drive_service = build("drive", "v3", credentials=creds)

        if not filename:
            date_str = datetime.now().strftime("%Y-%m-%d")
            filename = f"Competitive Intelligence Report — {date_str}"

        # Upload as plain text (Drive will convert to Doc)
        file_metadata = {
            "name": filename,
            "parents": [GOOGLE_DRIVE_FOLDER_ID],
            "mimeType": "application/vnd.google-apps.document",
        }

        media = MediaIoBaseUpload(
            io.BytesIO(report_markdown.encode("utf-8")),
            mimetype="text/plain",
            resumable=False,
        )

        file = drive_service.files().create(
            body=file_metadata,
            media_body=media,
            fields="id, webViewLink",
        ).execute()

        return file.get("webViewLink", "")

    except Exception as e:
        return f"[Drive upload failed: {str(e)}]"
