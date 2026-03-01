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
            style = paragraph.get("paragraphStyle", {}).get("namedStyleType", "")
            if style in ("HEADING_1", "HEADING_2", "HEADING_3"):
                lines.append(f"\n## {text}")
            else:
                lines.append(text)
    return "\n".join(lines)


def _extract_image_ids_from_body(content: list) -> list[str]:
    """
    Extract all inline image object IDs from a Google Doc body.
    These IDs are used to fetch the actual image bytes via Drive API.
    """
    image_ids = []
    for element in content:
        paragraph = element.get("paragraph")
        if not paragraph:
            continue
        for pe in paragraph.get("elements", []):
            inline_obj = pe.get("inlineObjectElement", {})
            obj_id = inline_obj.get("inlineObjectId")
            if obj_id:
                image_ids.append(obj_id)
    return image_ids


def _fetch_image_as_base64(object_id: str, inline_objects: dict) -> str | None:
    """
    Fetch an inline image from a Google Doc as a base64 string.
    Uses the image's source URI embedded in the doc metadata.
    """
    try:
        obj = inline_objects.get(object_id, {})
        embedded = obj.get("inlineObjectProperties", {}).get("embeddedObject", {})
        image_props = embedded.get("imageProperties", {})
        source_uri = image_props.get("sourceUri") or image_props.get("contentUri")

        if not source_uri:
            return None

        creds = get_google_creds()
        import google.auth.transport.requests
        authed_session = google.auth.transport.requests.AuthorizedSession(creds)
        response = authed_session.get(source_uri, timeout=15)

        if response.status_code == 200:
            import base64
            return base64.b64encode(response.content).decode("utf-8")

        return None

    except Exception:
        return None


def read_competitor_doc(doc_id: str) -> dict:
    """
    Read a single competitor Google Doc, including all tabs and inline images.
    Each tab is treated as a feature category group.

    Returns:
        {
            "text": "full text content with tab headers...",
            "images": ["base64str1", "base64str2", ...]   # one per inline image found
        }
    """
    try:
        creds = get_google_creds()
        docs_service = build("docs", "v1", credentials=creds)

        doc = docs_service.documents().get(
            documentId=doc_id,
            includeTabsContent=True,
        ).execute()

        # Inline objects map: used to resolve image base64
        inline_objects = doc.get("inlineObjects", {})
        all_text_parts = []
        all_image_ids = []

        # ── Multi-tab doc ──────────────────────────────────────────────────────
        tabs = doc.get("tabs", [])
        if tabs:
            for tab in tabs:
                child_tabs = tab.get("childTabs", [])
                tabs_to_read = [tab] + child_tabs

                for t in tabs_to_read:
                    doc_tab = t.get("documentTab", {})
                    body_content = doc_tab.get("body", {}).get("content", [])
                    if body_content:
                        tab_title = t.get("tabProperties", {}).get("title", "Notes")
                        tab_text = _extract_text_from_body(body_content)
                        if tab_text.strip():
                            all_text_parts.append(f"\n### Tab: {tab_title}\n{tab_text}")
                        all_image_ids.extend(_extract_image_ids_from_body(body_content))

        # ── Single-tab / no tabs fallback ──────────────────────────────────────
        if not all_text_parts:
            body_content = doc.get("body", {}).get("content", [])
            fallback_text = _extract_text_from_body(body_content)
            if fallback_text.strip():
                all_text_parts.append(fallback_text)
            all_image_ids.extend(_extract_image_ids_from_body(body_content))

        # ── Fetch images as base64 (cap at 10 to avoid token overload) ─────────
        images_base64 = []
        for obj_id in all_image_ids[:10]:
            b64 = _fetch_image_as_base64(obj_id, inline_objects)
            if b64:
                images_base64.append(b64)

        return {
            "text": "\n\n".join(all_text_parts),
            "images": images_base64,
        }

    except Exception as e:
        return {"text": f"[Could not read doc {doc_id}: {str(e)}]", "images": []}


def get_scrapbook_section(vendor_name: str) -> dict:
    """
    Find and read the Google Doc for a specific vendor from the scrapbook folder.
    Matches doc filename to vendor name (case-insensitive, partial match).
    Reads all tabs and extracts inline images.

    Folder structure expected:
        📁 Competitor Scrapbook/
            📄 Salesforce          ← filename matches vendor name
            📄 HubSpot
            📄 Zoho CRM

    Returns:
        {
            "text": "scrapbook notes text...",
            "images": ["base64img1", ...]
        }
    """
    docs = list_docs_in_scrapbook_folder()
    if not docs:
        return {"text": "", "images": []}

    vendor_lower = vendor_name.lower()

    matched_doc = None
    for doc in docs:
        if vendor_lower in doc["name"].lower() or doc["name"].lower() in vendor_lower:
            matched_doc = doc
            break

    if not matched_doc:
        return {"text": "", "images": []}

    result = read_competitor_doc(matched_doc["doc_id"])
    result["text"] = f"=== Scrapbook: {matched_doc['name']} ===\n{result['text']}"
    return result


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
