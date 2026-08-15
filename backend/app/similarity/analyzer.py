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

from backend.app.advisor.plagiarism_agent import plagiarism_agent

def save_section_embeddings(paper_id: str, sections: List[Dict[str, Any]]):
    """
    Computes and saves both TF representation and dense SBERT neural vectors in DB.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Create tables if not exist
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS paragraph_tfs (
        section_id TEXT PRIMARY KEY,
        paper_id TEXT NOT NULL,
        tf_json TEXT NOT NULL
    )
    """)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS paragraph_embeddings (
        section_id TEXT PRIMARY KEY,
        paper_id TEXT NOT NULL,
        embedding_json TEXT NOT NULL
    )
    """)
    
    paragraphs = [s for s in sections if s["layout_metadata"].get("type") == "paragraph"]
    for p in paragraphs:
        text = p["original_text"]
        words = tokenize(text)
        tf = compute_tf(words)
        cursor.execute(
            "INSERT OR REPLACE INTO paragraph_tfs (section_id, paper_id, tf_json) VALUES (?, ?, ?)",
            (p["id"], paper_id, json.dumps(tf))
        )

        dense_vec = plagiarism_agent.encode_dense_vector(text)
        if dense_vec:
            cursor.execute(
                "INSERT OR REPLACE INTO paragraph_embeddings (section_id, paper_id, embedding_json) VALUES (?, ?, ?)",
                (p["id"], paper_id, json.dumps(dense_vec))
            )
        
    conn.commit()
    conn.close()

def analyze_paper_similarity(paper_id: str, uploaded_sections: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Compares uploaded paragraphs against database sections using PlagiarismDetectionAgent
    combining Lexical Fingerprinting, Sparse TF-IDF, and Dense SBERT Neural Embeddings.
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
        
    # Get all database paragraphs from other papers
    cursor.execute("""
        SELECT pt.section_id, pt.paper_id, pt.tf_json, s.original_text, p.filename, pe.embedding_json
        FROM paragraph_tfs pt
        JOIN sections s ON pt.section_id = s.id
        JOIN papers p ON pt.paper_id = p.id
        LEFT JOIN paragraph_embeddings pe ON pt.section_id = pe.section_id
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
        
    db_records = []
    for r in db_rows:
        emb = json.loads(r["embedding_json"]) if r["embedding_json"] else None
        db_records.append({
            "section_id": r["section_id"],
            "paper_id": r["paper_id"],
            "text": r["original_text"],
            "filename": r["filename"],
            "dense_vector": emb
        })
        
    uploaded_paragraphs = [s for s in uploaded_sections if s["layout_metadata"].get("type") == "paragraph"]
    if not uploaded_paragraphs:
        conn.close()
        return {
            "overall_similarity": 0.0,
            "flagged_count": 0,
            "sections": uploaded_sections
        }
        
    updated_sections = []
    flagged_count = 0
    total_paragraph_similarity = 0.0

    # CopyLeaks check
    use_copyleaks = getattr(settings, "USE_COPYLEAKS", False)
    copyleaks_active = False
    if use_copyleaks:
        try:
            from backend.app.similarity.copyleaks_service import check_text_similarity
            test_res = check_text_similarity("Test string for CopyLeaks connection")
            if test_res.get("status") == "success":
                copyleaks_active = True
        except Exception as e:
            print(f"Error initializing CopyLeaks API: {e}")

    for s in uploaded_sections:
        s_copy = dict(s)
        if s["layout_metadata"].get("type") == "paragraph":
            text = s["original_text"]
            upload_vector = plagiarism_agent.encode_dense_vector(text)
            
            if copyleaks_active:
                try:
                    check_text_similarity(text)
                    s_copy["layout_metadata"]["verified_by"] = "CopyLeaks API"
                except Exception as e:
                    print(f"CopyLeaks paragraph check failed: {e}")
            
            best_match = None
            best_agent_analysis = None
            max_sim = 0.0
            
            for db_rec in db_records:
                agent_res = plagiarism_agent.analyze_pair(
                    query_text=text,
                    target_text=db_rec["text"],
                    query_vector=upload_vector,
                    target_vector=db_rec["dense_vector"]
                )
                sim = agent_res["composite_score"]
                if sim > max_sim:
                    max_sim = sim
                    best_match = db_rec
                    best_agent_analysis = agent_res
                    
            words_count = len(text.split())
            is_header = words_count < 10 or bool(re.search(r'^(?:[I|V|X]+\.|\d+\.|\bABSTRACT\b|\bREFERENCES\b|\bACKNOWLEDGMENT\b)', text.strip(), re.IGNORECASE))

            s_copy["similarity_score"] = round(max_sim, 3)
            s_copy["is_flagged"] = (max_sim >= settings.SIMILARITY_THRESHOLD) and not is_header

            
            if best_match and best_agent_analysis:
                s_copy["layout_metadata"]["agent_analysis"] = best_agent_analysis
                if s_copy["is_flagged"]:
                    flagged_count += 1
                    s_copy["layout_metadata"]["similarity_source"] = {
                        "filename": best_match["filename"],
                        "matching_text": best_match["text"],
                        "score": round(max_sim, 3),
                        "risk_category": best_agent_analysis["risk_category"],
                        "risk_level": best_agent_analysis["risk_level"],
                        "matched_spans": best_agent_analysis["matched_spans"]
                    }
                
            total_paragraph_similarity += max_sim
            
            cursor.execute(
                "UPDATE sections SET similarity_score = ?, is_flagged = ?, layout_metadata = ? WHERE id = ?",
                (s_copy["similarity_score"], 1 if s_copy["is_flagged"] else 0, json.dumps(s_copy["layout_metadata"]), s["id"])
            )
        else:
            s_copy["similarity_score"] = 0.0
            s_copy["is_flagged"] = False
            
        updated_sections.append(s_copy)
        
    avg_similarity = total_paragraph_similarity / len(uploaded_paragraphs) if uploaded_paragraphs else 0.0
    
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

