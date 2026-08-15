import sqlite3
import json
import os
from backend.app.config import settings

DB_PATH = settings.DATABASE_URL.replace("sqlite:///", "")

def get_db_connection():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False, timeout=30.0)
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Create papers table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS papers (
        id TEXT PRIMARY KEY,
        filename TEXT NOT NULL,
        original_format TEXT NOT NULL,
        status TEXT NOT NULL,
        overall_similarity REAL DEFAULT 0.0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    # Create sections table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS sections (
        id TEXT PRIMARY KEY,
        paper_id TEXT NOT NULL,
        section_name TEXT,
        original_text TEXT NOT NULL,
        rewritten_text TEXT,
        similarity_score REAL DEFAULT 0.0,
        is_flagged INTEGER DEFAULT 0,
        layout_metadata TEXT, -- JSON structure
        FOREIGN KEY (paper_id) REFERENCES papers (id) ON DELETE CASCADE
    )
    """)
    
    # Create references table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS references_list (
        id TEXT PRIMARY KEY,
        paper_id TEXT NOT NULL,
        raw_reference TEXT NOT NULL,
        citation_key TEXT,
        FOREIGN KEY (paper_id) REFERENCES papers (id) ON DELETE CASCADE
    )
    """)

    # Create paragraph_embeddings table for neural dense vectors
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS paragraph_embeddings (
        section_id TEXT PRIMARY KEY,
        paper_id TEXT NOT NULL,
        embedding_json TEXT NOT NULL,
        FOREIGN KEY (paper_id) REFERENCES papers (id) ON DELETE CASCADE
    )
    """)
    
    conn.commit()
    conn.close()

# Helper DB access methods
def create_paper(paper_id: str, filename: str, original_format: str):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO papers (id, filename, original_format, status) VALUES (?, ?, ?, ?)",
        (paper_id, filename, original_format, "uploaded")
    )
    conn.commit()
    conn.close()

def update_paper_status(paper_id: str, status: str, overall_similarity: float = 0.0):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE papers SET status = ?, overall_similarity = ? WHERE id = ?",
        (status, overall_similarity, paper_id)
    )
    conn.commit()
    conn.close()

def get_paper(paper_id: str):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM papers WHERE id = ?", (paper_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def get_all_papers():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM papers ORDER BY created_at DESC")
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def add_sections(sections_data: list):
    conn = get_db_connection()
    cursor = conn.cursor()
    for s in sections_data:
        cursor.execute(
            """INSERT INTO sections 
            (id, paper_id, section_name, original_text, rewritten_text, similarity_score, is_flagged, layout_metadata) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                s["id"],
                s["paper_id"],
                s.get("section_name"),
                s["original_text"],
                s.get("rewritten_text"),
                s.get("similarity_score", 0.0),
                1 if s.get("is_flagged") else 0,
                json.dumps(s.get("layout_metadata", {}))
            )
        )
    conn.commit()
    conn.close()

def update_section_rewrite(section_id: str, rewritten_text: str, similarity_score: float = 0.0, is_flagged: bool = False):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE sections SET rewritten_text = ?, similarity_score = ?, is_flagged = ? WHERE id = ?",
        (rewritten_text, similarity_score, 1 if is_flagged else 0, section_id)
    )
    conn.commit()
    conn.close()

def get_paper_sections(paper_id: str):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM sections WHERE paper_id = ?", (paper_id,))
    rows = cursor.fetchall()
    conn.close()
    
    sections = []
    for r in rows:
        d = dict(r)
        d["layout_metadata"] = json.loads(d["layout_metadata"]) if d["layout_metadata"] else {}
        d["is_flagged"] = bool(d["is_flagged"])
        sections.append(d)
    return sections

def get_section(section_id: str):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM sections WHERE id = ?", (section_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        d = dict(row)
        d["layout_metadata"] = json.loads(d["layout_metadata"]) if d["layout_metadata"] else {}
        d["is_flagged"] = bool(d["is_flagged"])
        return d
    return None

def add_references(paper_id: str, refs: list):
    conn = get_db_connection()
    cursor = conn.cursor()
    for idx, ref in enumerate(refs):
        if isinstance(ref, dict):
            raw = ref.get("raw_reference", str(ref))
            key = ref.get("citation_key")
        else:
            raw = str(ref)
            key = f"[{idx+1}]"
        cursor.execute(
            "INSERT INTO references_list (id, paper_id, raw_reference, citation_key) VALUES (?, ?, ?, ?)",
            (f"{paper_id}_ref_{idx}", paper_id, raw, key)
        )
    conn.commit()
    conn.close()

def get_paper_references(paper_id: str):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM references_list WHERE paper_id = ?", (paper_id,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def update_reference(ref_id: str, raw_reference: str, citation_key: str = None):
    conn = get_db_connection()
    cursor = conn.cursor()
    if citation_key:
        cursor.execute(
            "UPDATE references_list SET raw_reference = ?, citation_key = ? WHERE id = ?",
            (raw_reference, citation_key, ref_id)
        )
    else:
        cursor.execute(
            "UPDATE references_list SET raw_reference = ? WHERE id = ?",
            (raw_reference, ref_id)
        )
    conn.commit()
    conn.close()

