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


# ── Google Doc Reader ──────────────────────────────────────────────────────────

def read_scrapbook_doc(doc_id: str = None) -> dict[str, str]:
    """
    Read Google Doc scrapbook and parse into sections by competitor name.
    
    Expected Doc structure:
        # Salesforce
        ... notes ...
        
        # HubSpot
        ... notes ...
    
    Returns: {"Salesforce": "...", "HubSpot": "..."}
    """
    doc_id = doc_id or GOOGLE_DOC_SCRAPBOOK_ID
    if not doc_id:
        return {}

    try:
        creds = get_google_creds()
        service = build("docs", "v1", credentials=creds)
        doc = service.documents().get(documentId=doc_id).execute()

        sections: dict[str, list[str]] = {}
        current_section = None

        for element in doc.get("body", {}).get("content", []):
            paragraph = element.get("paragraph")
            if not paragraph:
                continue

            style = paragraph.get("paragraphStyle", {}).get("namedStyleType", "")
            text_runs = paragraph.get("elements", [])
            text = "".join(
                r.get("textRun", {}).get("content", "") for r in text_runs
            ).strip()

            if not text:
                continue

            # Heading 1 or 2 = new competitor section
            if style in ("HEADING_1", "HEADING_2"):
                current_section = text
                sections[current_section] = []
            elif current_section:
                sections[current_section].append(text)

        # Join paragraphs per section
        return {vendor: "\n".join(lines) for vendor, lines in sections.items()}

    except Exception as e:
        return {"error": f"Could not read scrapbook: {str(e)}"}


def get_scrapbook_section(vendor_name: str) -> str:
    """Get scrapbook notes for a specific vendor (case-insensitive partial match)."""
    all_sections = read_scrapbook_doc()
    vendor_lower = vendor_name.lower()

    for key, content in all_sections.items():
        if vendor_lower in key.lower():
            return content

    return ""


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
