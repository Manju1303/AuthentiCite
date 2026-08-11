import os
import asyncio
import logging
from backend.app.config import settings
from backend.app import database as db
from backend.app.parser import parse_document
from backend.app.similarity import analyze_paper_similarity, save_section_embeddings
from backend.app.similarity.citation_resolver import resolve_and_format_citation
from backend.app.chunker.chunk_manager import get_paragraph_with_context
from backend.app.rewrite import rewrite_text
from backend.app.quality import check_academic_quality
from backend.app.rebuild import rebuild_document

logger = logging.getLogger(__name__)

async def run_autonomous_pipeline(
    paper_id: str, 
    temp_path: str, 
    journal_format: str = "ieee"
):
    """
    Executes the entire document pipeline autonomously in the background:
    1. Parses document structure.
    2. Resolves citations online using Semantic Scholar.
    3. Analyzes similarity against the research database.
    4. Automatically rewrites flagged passages to reduce similarity.
    5. Rebuilds and exports the final document.
    """
    try:
        # Step 1: Parsing
        db.update_paper_status(paper_id, "parsing")
        parsed_data = parse_document(temp_path, media_dir=os.path.join(settings.UPLOAD_DIR, "media"))
        
        # Save parsed sections
        sections_to_add = []
        for sec in parsed_data["sections"]:
            sec["paper_id"] = paper_id
            sections_to_add.append(sec)
        if sections_to_add:
            db.add_sections(sections_to_add)
            
        # Save parsed raw references
        if parsed_data["references"]:
            db.add_references(paper_id, parsed_data["references"])
            
        # Save embeddings for future searches
        save_section_embeddings(paper_id, sections_to_add)
        
        # Step 2: Resolve Citations
        db.update_paper_status(paper_id, "resolving_citations")
        references = db.get_paper_references(paper_id)
        for idx, ref in enumerate(references):
            res = await resolve_and_format_citation(
                raw_reference=ref["raw_reference"],
                style="numeric" if journal_format == "ieee" else "author_year",
                citation_idx=idx + 1
            )
            if res["resolved"]:
                cit_key = f"DOI: {res['doi']}" if res["doi"] else ref["citation_key"]
                db.update_reference(ref["id"], res["formatted_reference"], cit_key)
                
        # Step 3: Run Similarity Check
        db.update_paper_status(paper_id, "checking_similarity")
        sections = db.get_paper_sections(paper_id)
        similarity_results = analyze_paper_similarity(paper_id, sections)
        
        # Step 4: AI Rewrites for Flagged Sections
        db.update_paper_status(paper_id, "rewriting")
        updated_sections = db.get_paper_sections(paper_id)
        flagged_sections = [s for s in updated_sections if s["is_flagged"]]
        
        if flagged_sections:
            for sec in flagged_sections:
                try:
                    target_idx = next(i for i, s in enumerate(updated_sections) if s["id"] == sec["id"])
                    context_info = get_paragraph_with_context(updated_sections, target_idx)
                    
                    # Rewrite text block
                    rewritten_text = rewrite_text(
                        text=context_info["text"],
                        context_before=context_info["context_before"],
                        context_after=context_info["context_after"],
                        target_similarity=settings.SIMILARITY_THRESHOLD
                    )
                    
                    # Validate quality metrics
                    quality_report = check_academic_quality(context_info["text"], rewritten_text)
                    meta = sec["layout_metadata"]
                    meta["quality_warnings"] = quality_report["warnings"]
                    
                    db.update_section_rewrite(sec["id"], rewritten_text, similarity_score=0.0, is_flagged=False)
                except Exception as e:
                    logger.error(f"Failed to auto-rewrite section {sec['id']}: {e}", exc_info=True)
                    
            # Recheck similarity after rewriting
            updated_sections = db.get_paper_sections(paper_id)
            analyze_paper_similarity(paper_id, updated_sections)
            
        # Step 5: Document Rebuild
        db.update_paper_status(paper_id, "rebuilding")
        final_sections = db.get_paper_sections(paper_id)
        final_references = db.get_paper_references(paper_id)
        layout_map = {"margins": {"top": 1.0, "bottom": 1.0, "left": 1.0, "right": 1.0}}
        output_filename = f"rebuilt_{paper_id}.docx"
        output_path = os.path.join(settings.OUTPUT_DIR, output_filename)
        
        rebuild_document(
            sections=final_sections,
            references=final_references,
            layout_map=layout_map,
            output_path=output_path,
            journal_format=journal_format,
            media_dir=os.path.join(settings.UPLOAD_DIR, "media")
        )
        
        db.update_paper_status(paper_id, "ready")
        logger.info(f"Autonomous pipeline completed successfully for paper {paper_id}")
        
    except Exception as e:
        logger.error(f"Error in autonomous pipeline worker for paper {paper_id}: {e}", exc_info=True)
        db.update_paper_status(paper_id, f"error: {str(e)}")
    finally:
        # Secure cleanup: Ensure the uploaded source manuscript file is always deleted from temp storage
        if os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except Exception as cleanup_err:
                logger.error(f"Failed to delete temporary file {temp_path}: {cleanup_err}", exc_info=True)
