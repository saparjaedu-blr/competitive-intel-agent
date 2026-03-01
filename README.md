# Competitive Intelligence Agent

An AI agent that monitors competitor websites, YouTube channels, and your personal Google Doc scrapbook — synthesizing everything into a structured intelligence report with weekly diffs. Built with LangGraph + GPT-4o + Streamlit.

---

## Features

- **Multi-source scraping**: Competitor websites, blogs, YouTube video transcripts
- **Personal scrapbook**: Reads your Google Doc (organized by competitor sections)
- **GPT-4o synthesis**: Structured analysis per vendor — launches, pricing, strategy, gaps
- **Diff engine**: Highlights only what's *new* since your last run
- **Google Drive output**: Auto-saves dated reports to your Drive folder
- **Email delivery**: Send reports to multiple recipients via Gmail

---

## Setup

### 1. Clone & install

```bash
git clone https://github.com/YOUR_USERNAME/competitive-intel-agent.git
cd competitive-intel-agent

python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

pip install -r requirements.txt
playwright install chromium
```

### 2. Configure environment

```bash
cp .env.example .env
# Edit .env with your API keys
```

### 3. Set up Google OAuth

1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Create a project → Enable **Google Drive API** and **Google Docs API**
3. Create OAuth 2.0 credentials → Download as `credentials.json`
4. Place `credentials.json` in the project root
5. First run will open a browser for Google auth — token saved as `token.json`

### 4. Gmail App Password

1. Enable 2-factor auth on your Google account
2. Go to [App Passwords](https://myaccount.google.com/apppasswords)
3. Generate a password for "Mail" → paste into `GMAIL_APP_PASSWORD` in `.env`

### 5. Google Doc Scrapbook structure

Create a folder in Google Drive called `Competitor Scrapbook` (or any name you prefer).

Inside that folder, create **one Google Doc per competitor** — the filename is the vendor name:

```
📁 Competitor Scrapbook/
    📄 Salesforce        ← filename must match the vendor name you configure in the app
    📄 HubSpot
    📄 Zoho CRM
```

Each doc can have **multiple tabs** to group features by category (e.g. "AI Features", "Pricing", "Integrations", "Roadmap"). The agent reads all tabs automatically.

Copy the **folder** ID from its URL (not the doc ID):
`https://drive.google.com/drive/folders/YOUR_FOLDER_ID_HERE`

Paste this as `GOOGLE_DOC_SCRAPBOOK_ID` in your `.env`.

> **Naming tip:** The doc filename matching is case-insensitive and partial — so a doc named "Salesforce CRM" will match a vendor configured as "Salesforce".

### 6. Run

```bash
streamlit run app.py
```

---

## Environment Variables

| Variable | Description |
|---|---|
| `OPENAI_API_KEY` | OpenAI API key |
| `GOOGLE_DRIVE_FOLDER_ID` | Drive folder ID for report output |
| `GOOGLE_DOC_SCRAPBOOK_ID` | Your scrapbook Google Doc ID |
| `GMAIL_SENDER` | Your Gmail address |
| `GMAIL_APP_PASSWORD` | Gmail App Password (16 chars) |
| `YOUTUBE_API_KEY` | *(Optional)* YouTube Data API v3 key for channel search |

---

## Project Structure

```
competitive-intel-agent/
├── app.py                    # Streamlit entry point
├── config/settings.py        # Env + constants
├── db/database.py            # SQLite CRUD
├── agent/
│   ├── graph.py              # LangGraph definition
│   ├── state.py              # AgentState TypedDict
│   └── nodes/                # One node per pipeline step
│       ├── web_scraper.py
│       ├── youtube_scraper.py
│       ├── gdoc_reader.py
│       ├── synthesizer.py
│       ├── diff_engine.py
│       └── report_writer.py
├── email/emailer.py          # Gmail SMTP
├── ui/pages/                 # Streamlit pages
│   ├── configure.py
│   ├── evaluate.py
│   └── history.py
└── reports/                  # Local report cache (gitignored)
```

---

## Adding to GitHub

```bash
git init
git add .
git commit -m "Initial commit — Competitive Intelligence Agent"
git remote add origin https://github.com/YOUR_USERNAME/competitive-intel-agent.git
git push -u origin main
```

`.env`, `token.json`, `credentials.json`, and `*.db` are all gitignored — your secrets stay local.
