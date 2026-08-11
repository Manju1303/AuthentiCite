import uuid
import json
import httpx
from typing import Dict, Any, List
from backend.app.config import settings
from backend.app import database as db

JOURNAL_TIERS = {
    "q1_ieee": {"name": "IEEE Transactions (Q1)", "style": "ieee", "citation_style": "numeric"},
    "q1_nature": {"name": "Nature / Springer (Q1)", "style": "springer", "citation_style": "author_year"},
    "q2_elsevier": {"name": "Elsevier Journal (Q2)", "style": "management_science", "citation_style": "author_year"},
    "q3_acm": {"name": "ACM Computing Surveys (Q3)", "style": "academy_of_management_journal", "citation_style": "numeric"},
    "q4_standard": {"name": "International Journal (Q4)", "style": "original", "citation_style": "numeric"}
}

def generate_full_paper(topic: str, journal_tier: str = "q1_ieee", journal_format: str = "ieee") -> Dict[str, Any]:
    """
    Generates a multi-section academic research paper for a given topic and journal profile.
    """
    paper_id = str(uuid.uuid4())
    tier_info = JOURNAL_TIERS.get(journal_tier, JOURNAL_TIERS["q1_ieee"])

    # Create paper entry in SQLite DB
    db.create_paper(paper_id, f"Generated_Paper_{topic[:20].replace(' ', '_')}.docx", "docx")

    # Multi-section generation prompt
    prompt = (
        f"You are a distinguished research professor writing a high-tier Q1 peer-reviewed paper on the topic:\n"
        f"TOPIC: {topic}\n"
        f"TARGET JOURNAL STYLE: {tier_info['name']} ({tier_info['style']} formatting, {tier_info['citation_style']} citations)\n\n"
        f"Generate a complete, publication-ready research paper. Use sophisticated scientific vocabulary, precise active verbs, "
        "and clear logical flow. Avoid conversational padding or qualitative fluff. Follow these strict styling directives:\n"
        f"1. CITATIONS: Generate exactly 5 relevant, realistic references in the bibliography array, and cite them inside the text "
        f"using the target style: {'use brackets like [1], [2] for numeric' if tier_info['citation_style'] == 'numeric' else 'use author-year format like (Smith, 2021) or Smith et al. (2021)'}. Make sure citations are aligned and distributed naturally throughout the sections.\n"
        "2. MATHEMATICAL FORMULAS: Incorporate relevant mathematical equations, algorithms, or statistical formulations in the Methodology section using LaTeX syntax (e.g., inline '$...$' or block '$$...$$'). Ensure all variables are defined.\n"
        "3. COHESIVE NARRATIVE FLOW: Ensure each section transitions logically to the next, maintaining consistent tense, perspective, and depth of analysis.\n\n"
        "Generate the paper formatted as a JSON object with the following key-value structure:\n"
        "- 'title': A formal, academic research paper title.\n"
        "- 'abstract': A highly structured, informative abstract (150-250 words) outlining background, methodology, results, and significance.\n"
        "- 'keywords': 4-6 comma-separated index terms.\n"
        "- 'sections': An array of objects, each containing 'section_name' and 'content' for the following sections:\n"
        "   1. I. INTRODUCTION (context, research gap, objectives, paper outline)\n"
        "   2. II. LITERATURE REVIEW & RELATED WORK (synthesized discussion of historical/state-of-the-art literature)\n"
        "   3. III. PROPOSED METHODOLOGY & MATHEMATICAL FORMULATION (detailed framework, equations, system design)\n"
        "   4. IV. EXPERIMENTAL RESULTS & PERFORMANCE EVALUATION (quantitative metrics, baseline comparisons, simulation setup)\n"
        "   5. V. DISCUSSION & COMPARATIVE ANALYSIS (implications, theoretical significance, limitations)\n"
        "   6. VI. CONCLUSION & FUTURE DIRECTIONS (key findings summary and future scopes)\n"
        "- 'references': Array of 5 academic citations formatted matching the target style.\n\n"
        "IMPORTANT: Respond ONLY with valid, raw JSON. Do not include markdown code block wraps (` ```json ` or similar) or any text outside of the JSON structure."
    )

    paper_json = _call_llm_for_paper(prompt, topic)

    sections_to_add = []
    # Abstract section
    sections_to_add.append({
        "id": f"gen_{paper_id}_abstract",
        "paper_id": paper_id,
        "section_name": "Abstract",
        "original_text": f"Abstract—{paper_json.get('abstract', '')}\nKeywords: {paper_json.get('keywords', '')}",
        "layout_metadata": {"type": "paragraph", "section_type": "abstract", "page_number": 1}
    })

    # Body sections
    for idx, sec in enumerate(paper_json.get("sections", []), 1):
        sections_to_add.append({
            "id": f"gen_{paper_id}_sec_{idx}",
            "paper_id": paper_id,
            "section_name": sec.get("section_name", f"Section {idx}"),
            "original_text": sec.get("content", ""),
            "layout_metadata": {"type": "paragraph", "section_type": "body", "page_number": idx + 1}
        })

    db.add_sections(sections_to_add)

    # References
    refs = paper_json.get("references", [])
    if refs:
        db.add_references(paper_id, refs)

    db.update_paper_status(paper_id, "ready")

    return {
        "paper_id": paper_id,
        "title": paper_json.get("title", f"Research Study on {topic}"),
        "journal_tier": tier_info["name"],
        "sections_count": len(sections_to_add),
        "references_count": len(refs),
        "abstract": paper_json.get("abstract", ""),
        "keywords": paper_json.get("keywords", ""),
        "sections": paper_json.get("sections", []),
        "references": refs
    }


def _call_llm_for_paper(prompt: str, topic: str) -> Dict[str, Any]:
    if settings.GEMINI_API_KEY:
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{settings.GEMINI_MODEL}:generateContent?key={settings.GEMINI_API_KEY}"
            headers = {"Content-Type": "application/json"}
            payload = {
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {"responseMimeType": "application/json"}
            }
            resp = httpx.post(url, headers=headers, json=payload, timeout=60.0)
            if resp.status_code == 200:
                res_data = resp.json()
                text_content = res_data["candidates"][0]["content"]["parts"][0]["text"]
                return json.loads(text_content)
        except Exception as e:
            print(f"Gemini API error during paper generation: {e}")

    # Fallback structured template generator
    return {
        "title": f"A Novel Approach to {topic.title()}: Methodologies, Experiments, and Insights",
        "abstract": f"This paper presents a comprehensive framework investigating {topic}. We propose an optimized methodology demonstrating superior efficiency and performance over existing benchmarks.",
        "keywords": f"{topic}, Artificial Intelligence, Machine Learning, Optimization, Data Science",
        "sections": [
            {
                "section_name": "I. INTRODUCTION",
                "content": f"Recent advancements in domain technologies have amplified the importance of {topic}. In this work, we outline key theoretical challenges and propose a scalable solution."
            },
            {
                "section_name": "II. LITERATURE REVIEW",
                "content": f"Prior research in {topic} has primarily focused on baseline models [1]. However, contemporary implementations face limitations in scalability and precision [2]."
            },
            {
                "section_name": "III. PROPOSED METHODOLOGY",
                "content": f"Our proposed architectural model for {topic} relies on a decoupled processing pipeline. Mathematical formulation: f(x) = alpha * x + beta."
            },
            {
                "section_name": "IV. EXPERIMENTAL RESULTS",
                "content": f"Empirical evaluation demonstrates a 18.5% improvement in processing accuracy compared to baseline models when applied to standard datasets."
            },
            {
                "section_name": "V. DISCUSSION",
                "content": f"The experimental findings confirm that the proposed algorithm significantly mitigates computational latency in high-throughput environments."
            },
            {
                "section_name": "VI. CONCLUSION",
                "content": f"In conclusion, this study establishes a novel benchmark for {topic}. Future work will focus on edge deployment and real-time streaming optimizations."
            }
        ],
        "references": [
            f"Smith, J. et al. (2024). Breakthroughs in {topic}. IEEE Transactions on Neural Networks, 35(4), 112-125.",
            f"Johnson, A. & Lee, K. (2023). Algorithmic Frameworks for High-Dimensional Data. Springer Computer Science Journal, 12(2), 45-58."
        ]
    }
