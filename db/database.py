import sqlite3
import json
from datetime import datetime
from config.settings import DB_PATH


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.executescript("""
        CREATE TABLE IF NOT EXISTS competitors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            vendor_name TEXT NOT NULL UNIQUE,
            website_url TEXT,
            blog_url TEXT,
            youtube_channel TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            run_date TEXT NOT NULL,
            research_query TEXT,
            vendors_covered TEXT,
            report_markdown TEXT,
            gdrive_link TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS diff_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            report_id INTEGER REFERENCES reports(id),
            vendor_name TEXT,
            previous_snapshot TEXT,
            new_snapshot TEXT,
            delta_summary TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    conn.commit()
    conn.close()


# ── Competitor CRUD ────────────────────────────────────────────────────────────

def add_competitor(vendor_name, website_url="", blog_url="", youtube_channel=""):
    conn = get_connection()
    try:
        conn.execute(
            """INSERT INTO competitors (vendor_name, website_url, blog_url, youtube_channel)
               VALUES (?, ?, ?, ?)""",
            (vendor_name, website_url, blog_url, youtube_channel),
        )
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False  # duplicate vendor name
    finally:
        conn.close()


def update_competitor(competitor_id, vendor_name, website_url, blog_url, youtube_channel):
    conn = get_connection()
    conn.execute(
        """UPDATE competitors SET vendor_name=?, website_url=?, blog_url=?, youtube_channel=?
           WHERE id=?""",
        (vendor_name, website_url, blog_url, youtube_channel, competitor_id),
    )
    conn.commit()
    conn.close()


def delete_competitor(competitor_id):
    conn = get_connection()
    conn.execute("DELETE FROM competitors WHERE id=?", (competitor_id,))
    conn.commit()
    conn.close()


def get_all_competitors():
    conn = get_connection()
    rows = conn.execute("SELECT * FROM competitors ORDER BY vendor_name").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_competitor_by_name(vendor_name):
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM competitors WHERE vendor_name=?", (vendor_name,)
    ).fetchone()
    conn.close()
    return dict(row) if row else None


# ── Reports ────────────────────────────────────────────────────────────────────

def save_report(research_query, vendors_covered, report_markdown, gdrive_link=""):
    conn = get_connection()
    run_date = datetime.now().strftime("%Y-%m-%d %H:%M")
    cursor = conn.execute(
        """INSERT INTO reports (run_date, research_query, vendors_covered, report_markdown, gdrive_link)
           VALUES (?, ?, ?, ?, ?)""",
        (run_date, research_query, json.dumps(vendors_covered), report_markdown, gdrive_link),
    )
    report_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return report_id


def get_all_reports():
    conn = get_connection()
    rows = conn.execute("SELECT * FROM reports ORDER BY created_at DESC").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_report_by_id(report_id):
    conn = get_connection()
    row = conn.execute("SELECT * FROM reports WHERE id=?", (report_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def get_last_report_for_vendor(vendor_name):
    """Returns the most recent synthesis snapshot for a vendor from diff_log."""
    conn = get_connection()
    row = conn.execute(
        """SELECT new_snapshot, created_at FROM diff_log
           WHERE vendor_name=?
           ORDER BY created_at DESC LIMIT 1""",
        (vendor_name,),
    ).fetchone()
    conn.close()
    return dict(row) if row else None


# ── Diff Log ───────────────────────────────────────────────────────────────────

def save_diff_log(report_id, vendor_name, previous_snapshot, new_snapshot, delta_summary):
    conn = get_connection()
    conn.execute(
        """INSERT INTO diff_log (report_id, vendor_name, previous_snapshot, new_snapshot, delta_summary)
           VALUES (?, ?, ?, ?, ?)""",
        (report_id, vendor_name, previous_snapshot, new_snapshot, delta_summary),
    )
    conn.commit()
    conn.close()
