import os
import math
import re
import sqlite3
import json
from typing import List, Dict, Any
from backend.app.config import settings
from backend.app.database import get_db_connection

def tokenize(text: str) -> List[str]:
    """Tokenizes text into a list of lowercase alphanumeric words."""
    words = re.findall(r'\b\w+\b', text.lower())
    # Filter out very short words
    return [w for w in words if len(w) > 1]

def compute_tf(words: List[str]) -> Dict[str, float]:
    """Computes Term Frequency (TF) for a tokenized text."""
    if not words:
        return {}
    tf = {}
    for w in words:
        tf[w] = tf.get(w, 0.0) + 1.0
    # Normalize by total words
    total = float(len(words))
    for w in tf:
        tf[w] = tf[w] / total
    return tf

def compute_cosine_similarity(vec1: Dict[str, float], vec2: Dict[str, float]) -> float:
    """Computes Cosine Similarity between two TF-IDF sparse vectors."""
    intersection = set(vec1.keys()) & set(vec2.keys())
    if not intersection:
        return 0.0
        
    dot_product = sum(vec1[w] * vec2[w] for w in intersection)
    
    sum1 = sum(val ** 2 for val in vec1.values())
    sum2 = sum(val ** 2 for val in vec2.values())
    
    magnitude = math.sqrt(sum1) * math.sqrt(sum2)
    if not magnitude:
        return 0.0
        
    return dot_product / magnitude

def save_section_embeddings(paper_id: str, sections: List[Dict[str, Any]]):
    """
    Computes and saves TF representation in the database.
    Since we are using TF-IDF, we store the TF dictionary as a JSON string in a blob or text column.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Create the TF table if it doesn't exist
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS paragraph_tfs (
        section_id TEXT PRIMARY KEY,
        paper_id TEXT NOT NULL,
        tf_json TEXT NOT NULL
    )
    """)
    
    paragraphs = [s for s in sections if s["layout_metadata"].get("type") == "paragraph"]
    for p in paragraphs:
        words = tokenize(p["original_text"])
        tf = compute_tf(words)
        cursor.execute(
            "INSERT OR REPLACE INTO paragraph_tfs (section_id, paper_id, tf_json) VALUES (?, ?, ?)",
            (p["id"], paper_id, json.dumps(tf))
        )
        
    conn.commit()
    conn.close()

def analyze_paper_similarity(paper_id: str, uploaded_sections: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Compares all paragraphs in the uploaded paper against all other papers in the DB
    using TF-IDF Cosine Similarity in pure Python.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Ensure paragraph_tfs table exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='paragraph_tfs'")
    if not cursor.fetchone():
        conn.close()
        return {
            "overall_similarity": 0.0,
            "flagged_count": 0,
            "sections": [dict(s, similarity_score=0.0, is_flagged=False) for s in uploaded_sections]
        }
        
    # Get all TF vectors for other papers
    cursor.execute("""
        SELECT pt.section_id, pt.paper_id, pt.tf_json, s.original_text, p.filename
        FROM paragraph_tfs pt
        JOIN sections s ON pt.section_id = s.id
        JOIN papers p ON pt.paper_id = p.id
        WHERE pt.paper_id != ?
    """, (paper_id,))
    
    db_rows = cursor.fetchall()
    if not db_rows:
        conn.close()
        return {
            "overall_similarity": 0.0,
            "flagged_count": 0,
            "sections": [dict(s, similarity_score=0.0, is_flagged=False) for s in uploaded_sections]
        }
        
    # Reconstruct DB vectors and build Document Frequency (DF) map
    db_vectors = []
    df_map = {}
    total_docs = len(db_rows)
    
    for r in db_rows:
        tf = json.loads(r["tf_json"])
        db_vectors.append({
            "section_id": r["section_id"],
            "paper_id": r["paper_id"],
            "tf": tf,
            "text": r["original_text"],
            "filename": r["filename"]
        })
        for word in tf.keys():
            df_map[word] = df_map.get(word, 0.0) + 1.0
            
    # Parse uploaded paragraphs and compute their TFs
    uploaded_paragraphs = [s for s in uploaded_sections if s["layout_metadata"].get("type") == "paragraph"]
    if not uploaded_paragraphs:
        conn.close()
        return {
            "overall_similarity": 0.0,
            "flagged_count": 0,
            "sections": uploaded_sections
        }
        
    upload_tfs = {}
    for p in uploaded_paragraphs:
        words = tokenize(p["original_text"])
        upload_tfs[p["id"]] = compute_tf(words)
        # Include uploaded words in DF map for IDF calculation
        for word in upload_tfs[p["id"]].keys():
            df_map[word] = df_map.get(word, 0.0) + 1.0
            
    # Calculate IDF for all words
    idf_map = {}
    n_docs = total_docs + len(uploaded_paragraphs)
    for word, df in df_map.items():
        idf_map[word] = math.log(1.0 + (n_docs / (1.0 + df)))
        
    # Helper to compute TF-IDF vector from TF dict
    def get_tfidf_vector(tf_dict: Dict[str, float]) -> Dict[str, float]:
        tfidf = {}
        for w, tf_val in tf_dict.items():
            tfidf[w] = tf_val * idf_map.get(w, 0.0)
        return tfidf

    # Calculate TF-IDF vectors for database
    db_tfidf_vectors = []
    for db_vec in db_vectors:
        db_tfidf_vectors.append({
            "section_id": db_vec["section_id"],
            "paper_id": db_vec["paper_id"],
            "tfidf": get_tfidf_vector(db_vec["tf"]),
            "text": db_vec["text"],
            "filename": db_vec["filename"]
        })
        
    updated_sections = []
    flagged_count = 0
    total_paragraph_similarity = 0.0
    
    for s in uploaded_sections:
        s_copy = dict(s)
        if s["layout_metadata"].get("type") == "paragraph" and s["id"] in upload_tfs:
            upload_tfidf = get_tfidf_vector(upload_tfs[s["id"]])
            
            # Compute cosine similarity against all database TF-IDF vectors
            max_sim = 0.0
            best_match = None
            
            for db_tfidf in db_tfidf_vectors:
                sim = compute_cosine_similarity(upload_tfidf, db_tfidf["tfidf"])
                if sim > max_sim:
                    max_sim = sim
                    best_match = db_tfidf
                    
            s_copy["similarity_score"] = round(max_sim, 3)
            s_copy["is_flagged"] = max_sim >= settings.SIMILARITY_THRESHOLD
            
            if s_copy["is_flagged"] and best_match:
                flagged_count += 1
                s_copy["layout_metadata"]["similarity_source"] = {
                    "filename": best_match["filename"],
                    "matching_text": best_match["text"],
                    "score": round(max_sim, 3)
                }
                
            total_paragraph_similarity += max_sim
            
            # Save analysis results back to database
            cursor.execute(
                "UPDATE sections SET similarity_score = ?, is_flagged = ?, layout_metadata = ? WHERE id = ?",
                (s_copy["similarity_score"], 1 if s_copy["is_flagged"] else 0, json.dumps(s_copy["layout_metadata"]), s["id"])
            )
        else:
            s_copy["similarity_score"] = 0.0
            s_copy["is_flagged"] = False
            
        updated_sections.append(s_copy)
        
    # Calculate overall paper similarity
    avg_similarity = total_paragraph_similarity / len(uploaded_paragraphs) if uploaded_paragraphs else 0.0
    
    # Save overall score to paper
    cursor.execute(
        "UPDATE papers SET overall_similarity = ? WHERE id = ?",
        (round(avg_similarity, 3), paper_id)
    )
    
    conn.commit()
    conn.close()
    
    return {
        "overall_similarity": round(avg_similarity, 3),
        "flagged_count": flagged_count,
        "sections": updated_sections
    }
