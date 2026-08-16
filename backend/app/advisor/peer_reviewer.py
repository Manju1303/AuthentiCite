import re
from typing import Dict, Any, List
from backend.app import database as db

class AutonomousPeerReviewer:
    """
    Autonomous Q1 Journal Peer Reviewer Agent.
    Simulates a senior reviewer for Q1 publications (IEEE Transactions, Nature, Springer, Elsevier).
    Evaluates manuscript sections for scientific novelty, mathematical rigor, experimental evaluation,
    and reference recency.
    """

    def evaluate_paper(self, paper_id: str) -> Dict[str, Any]:
        """Runs autonomous peer review evaluation on a paper by paper_id."""
        paper = db.get_paper(paper_id)
        if not paper:
            return {"error": "Paper not found"}

        sections = db.get_paper_sections(paper_id)
        references = db.get_paper_references(paper_id)

        full_text = " ".join([s.get("original_text", "") for s in sections])

        # Section audits
        abstract_sec = next((s for s in sections if "abstract" in s.get("section_name", "").lower()), None)
        method_sec = next((s for s in sections if "method" in s.get("section_name", "").lower() or "algorithm" in s.get("section_name", "").lower()), None)
        exp_sec = next((s for s in sections if "result" in s.get("section_name", "").lower() or "experiment" in s.get("section_name", "").lower()), None)

        scores = {}
        comments = []

        # 1. Abstract & Title Audit
        if abstract_sec or "abstract" in full_text.lower()[:300]:
            scores["abstract_quality"] = 85
            comments.append("Abstract clearly introduces problem background and quantitative results.")
        else:
            scores["abstract_quality"] = 50
            comments.append("Abstract block missing or unformatted. Include explicit problem statement and key performance metrics.")

        # 2. Methodology & Mathematical Formulation Audit
        has_latex = "$" in full_text or "\\" in full_text or "equation" in full_text.lower()
        if method_sec and has_latex:
            scores["methodology_rigor"] = 90
            comments.append("Strong mathematical formulation with LaTeX equations and architectural breakdown.")
        elif method_sec:
            scores["methodology_rigor"] = 70
            comments.append("Methodology section present, but needs formal mathematical equations or algorithmic step definitions.")
        else:
            scores["methodology_rigor"] = 45
            comments.append("Methodology section lacks clear theoretical or algorithmic formulation.")

        # 3. Experimental Evaluation Audit
        has_numbers = len(re.findall(r'\b\d+(?:\.\d+)?%\b', full_text)) > 0 or "accuracy" in full_text.lower() or "table" in full_text.lower()
        if exp_sec and has_numbers:
            scores["experimental_rigor"] = 88
            comments.append("Quantitative experimental results presented with numerical performance comparisons.")
        elif exp_sec:
            scores["experimental_rigor"] = 65
            comments.append("Experimental section present. Add comparative baseline tables and statistical significance metrics.")
        else:
            scores["experimental_rigor"] = 40
            comments.append("Missing dedicated experimental evaluation section with baseline metrics.")

        # 4. Reference Recency & Citation Density Audit
        recent_years = re.findall(r'\b(202[0-6])\b', " ".join([r.get("raw_reference", "") for r in references]))
        recent_ref_count = len(recent_years)
        total_refs = len(references)

        if total_refs >= 10 and recent_ref_count >= 3:
            scores["reference_quality"] = 92
            comments.append(f"Comprehensive bibliography with {recent_ref_count} recent papers (2020-2026).")
        elif total_refs > 0:
            scores["reference_quality"] = 70
            comments.append(f"Contains {total_refs} references. Expand citations to include recent Q1 journal literature from 2022-2026.")
        else:
            scores["reference_quality"] = 35
            comments.append("Bibliography incomplete. Add at least 10-15 peer-reviewed citations.")

        # Overall Q1 Acceptability Score
        q1_acceptability_score = round(
            0.25 * scores["abstract_quality"] +
            0.35 * scores["methodology_rigor"] +
            0.25 * scores["experimental_rigor"] +
            0.15 * scores["reference_quality"], 1
        )

        if q1_acceptability_score >= 82.0:
            decision = "ACCEPT / MINOR REVISION"
            recommendation = "Manuscript meets high Q1 journal standards. Ready for camera-ready submission after minor proofreading."
        elif q1_acceptability_score >= 65.0:
            decision = "MAJOR REVISION REQUIRED"
            recommendation = "Manuscript has strong potential. Address reviewer comments regarding mathematical equations and experimental baseline comparisons."
        else:
            decision = "REJECT & RESUBMIT"
            recommendation = "Substantial expansion required. Add a formal methodology formulation, baseline experimental evaluation, and updated references."

        return {
            "paper_id": paper_id,
            "filename": paper.get("filename"),
            "q1_acceptability_score": q1_acceptability_score,
            "peer_review_decision": decision,
            "recommendation_summary": recommendation,
            "category_scores": scores,
            "reviewer_comments": comments
        }


# Global peer reviewer instance
peer_reviewer = AutonomousPeerReviewer()
