from typing import Dict, Any, List
from backend.app import database as db

def generate_reduction_advice(paper_id: str) -> Dict[str, Any]:
    """
    Generates actionable plagiarism reduction recommendations for a given paper.
    """
    paper = db.get_paper(paper_id)
    if not paper:
        return {"error": "Paper not found"}

    sections = db.get_paper_sections(paper_id)
    flagged_sections = [s for s in sections if s.get("is_flagged")]
    
    recommendations = []

    for s in flagged_sections:
        score = s.get("similarity_score", 0.0)
        meta = s.get("layout_metadata", {})
        match_src = meta.get("similarity_source", {})
        agent_analysis = meta.get("agent_analysis", {})
        text = s.get("original_text", "")

        action = "Rewrite Paragraph"
        tactics = []

        risk_cat = agent_analysis.get("risk_category", "Direct Plagiarism")
        
        if "Paraphrased" in risk_cat:
            action = "Deep Paraphrase Structural Re-ordering"
            tactics.append("Invert sentence structure and expand technical methodology context.")
            tactics.append("Replace domain synonyms while maintaining original technical intent.")
        elif score > 0.40:
            action = "Major Structural Reorganization"
            tactics.append("Convert passive sentences to active voice and split compound clauses.")
            tactics.append("Insert domain-specific citations [e.g. [1]] to ground verbatim matches.")
        elif score > 0.20:
            action = "Selective Paraphrasing & Synonym Substitution"
            tactics.append("Substitute non-technical general phrases while keeping specialized terminology.")
            tactics.append("Re-order introductory clauses.")

        if "latex" in text.lower() or "$" in text or "=" in text:
            tactics.append("Shield LaTeX equations and mathematical variables from modification.")

        recommendations.append({
            "section_id": s["id"],
            "section_name": s.get("section_name", "Paragraph Block"),
            "similarity_score": round(score * 100, 1),
            "match_source_file": match_src.get("filename") if match_src else "Internal Corpus Match",
            "risk_category": risk_cat,
            "risk_level": agent_analysis.get("risk_level", "HIGH"),
            "semantic_score": round(agent_analysis.get("semantic_score", 0.0) * 100, 1),
            "lexical_score": round(agent_analysis.get("lexical_score", 0.0) * 100, 1),
            "matched_spans": agent_analysis.get("matched_spans", match_src.get("matched_spans", [])),
            "recommended_action": action,
            "tactics": tactics,
            "snippet": text[:120] + "..." if len(text) > 120 else text
        })

    overall_similarity = round(paper.get("overall_similarity", 0.0) * 100, 1)

    strategy_summary = (
        f"Your paper has an overall similarity index of {overall_similarity}%. "
        f"We identified {len(flagged_sections)} high-risk paragraph blocks exceeding threshold. "
        f"Multi-stage agent detection evaluated lexical fingerprints & SBERT neural embeddings to pinpoint risk areas."
    )

    return {
        "paper_id": paper_id,
        "filename": paper.get("filename"),
        "overall_similarity": overall_similarity,
        "flagged_count": len(flagged_sections),
        "strategy_summary": strategy_summary,
        "recommendations": recommendations
    }

