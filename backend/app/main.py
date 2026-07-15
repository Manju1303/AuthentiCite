import os
import uuid
import shutil
from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from typing import List, Dict, Any, Optional

from backend.app.config import settings
from backend.app import database as db
from backend.app.models import (
    PaperResponse, 
    PaperAnalysisResponse, 
    SectionRewriteRequest, 
    PaperRewriteRequest,
    SectionResponse
)
from backend.app.parser import parse_document
from backend.app.chunker.chunk_manager import get_paragraph_with_context
from backend.app.similarity import analyze_paper_similarity, save_section_embeddings
from backend.app.rewrite import rewrite_text
from backend.app.quality import check_academic_quality
from backend.app.rebuild import rebuild_document
from backend.app.export.exporter import convert_docx_to_pdf

app = FastAPI(title=settings.PROJECT_NAME)

# Setup CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def startup_event():
    db.init_db()

@app.post("/api/v1/papers/upload", response_model=PaperResponse)
async def upload_paper(file: UploadFile = File(...)):
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in [".docx", ".pdf"]:
        raise HTTPException(status_code=400, detail="Only DOCX and PDF files are supported.")
        
    paper_id = str(uuid.uuid4())
    temp_filename = f"{paper_id}{ext}"
    temp_path = os.path.join(settings.UPLOAD_DIR, temp_filename)
    
    with open(temp_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    try:
        # Create paper record in DB
        db.create_paper(paper_id, file.filename, ext.strip("."))
        
        # Parse document structure
        parsed_data = parse_document(temp_path, media_dir=os.path.join(settings.UPLOAD_DIR, "media"))
        
        # Add sections to DB
        sections_to_add = []
        for sec in parsed_data["sections"]:
            sec["paper_id"] = paper_id
            sections_to_add.append(sec)
            
        if sections_to_add:
            db.add_sections(sections_to_add)
            
        # Add references to DB
        if parsed_data["references"]:
            db.add_references(paper_id, parsed_data["references"])
            
        # Save embeddings for future similarity searches against other uploads
        save_section_embeddings(paper_id, sections_to_add)
        
        db.update_paper_status(paper_id, "parsed")
        
        return db.get_paper(paper_id)
    except Exception as e:
        # Clean up on failure
        if os.path.exists(temp_path):
            os.remove(temp_path)
        db.update_paper_status(paper_id, f"error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to process document: {str(e)}")

@app.get("/api/v1/papers", response_model=List[PaperResponse])
def get_papers():
    return db.get_all_papers()

@app.get("/api/v1/papers/{paper_id}", response_model=PaperAnalysisResponse)
def get_paper_details(paper_id: str):
    paper = db.get_paper(paper_id)
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found.")
        
    sections = db.get_paper_sections(paper_id)
    references = db.get_paper_references(paper_id)
    
    return {
        "paper": paper,
        "sections": sections,
        "references": references
    }

@app.post("/api/v1/papers/{paper_id}/analyze")
def run_similarity_analysis(paper_id: str):
    paper = db.get_paper(paper_id)
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found.")
        
    sections = db.get_paper_sections(paper_id)
    if not sections:
        raise HTTPException(status_code=400, detail="Paper contains no text blocks to analyze.")
        
    # Analyze similarity against other papers
    result = analyze_paper_similarity(paper_id, sections)
    return {
        "overall_similarity": result["overall_similarity"],
        "flagged_count": result["flagged_count"]
    }

@app.post("/api/v1/sections/{section_id}/rewrite", response_model=SectionResponse)
def rewrite_section(section_id: str, request: SectionRewriteRequest):
    section = db.get_section(section_id)
    if not section:
        raise HTTPException(status_code=404, detail="Section not found.")
        
    # Get paragraph with context for LLM rewriter
    sections = db.get_paper_sections(section["paper_id"])
    target_idx = next(i for i, s in enumerate(sections) if s["id"] == section_id)
    context_info = get_paragraph_with_context(sections, target_idx)
    
    # Run LLM rewrite
    rewritten_text = rewrite_text(
        text=context_info["text"],
        context_before=context_info["context_before"],
        context_after=context_info["context_after"],
        target_similarity=settings.SIMILARITY_THRESHOLD
    )
    
    # Run quality validation
    quality_report = check_academic_quality(context_info["text"], rewritten_text)
    
    # Update layout metadata with warnings if any
    meta = section["layout_metadata"]
    meta["quality_warnings"] = quality_report["warnings"]
    
    # Save rewrite to DB (reset similarity score for re-checking)
    db.update_section_rewrite(section_id, rewritten_text, similarity_score=0.0, is_flagged=False)
    
    return db.get_section(section_id)

@app.post("/api/v1/papers/{paper_id}/rewrite-all")
def rewrite_flagged_sections(paper_id: str, background_tasks: BackgroundTasks):
    paper = db.get_paper(paper_id)
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found.")
        
    sections = db.get_paper_sections(paper_id)
    flagged_sections = [s for s in sections if s["is_flagged"]]
    
    if not flagged_sections:
        return {"message": "No flagged sections found to rewrite."}
        
    def process_bulk_rewrites():
        db.update_paper_status(paper_id, "rewriting")
        for idx, sec in enumerate(flagged_sections):
            try:
                target_idx = next(i for i, s in enumerate(sections) if s["id"] == sec["id"])
                context_info = get_paragraph_with_context(sections, target_idx)
                
                # Rewrite text
                rewritten_text = rewrite_text(
                    text=context_info["text"],
                    context_before=context_info["context_before"],
                    context_after=context_info["context_after"]
                )
                
                # Check quality
                quality_report = check_academic_quality(context_info["text"], rewritten_text)
                meta = sec["layout_metadata"]
                meta["quality_warnings"] = quality_report["warnings"]
                
                db.update_section_rewrite(sec["id"], rewritten_text, similarity_score=0.0, is_flagged=False)
            except Exception as e:
                print(f"Error bulk rewriting section {sec['id']}: {e}")
                
        # Run similarity recheck after all rewrites are complete
        updated_sections = db.get_paper_sections(paper_id)
        analyze_paper_similarity(paper_id, updated_sections)
        db.update_paper_status(paper_id, "ready")

    background_tasks.add_task(process_bulk_rewrites)
    return {"message": f"Started background rewrite of {len(flagged_sections)} flagged sections."}

@app.post("/api/v1/papers/{paper_id}/rebuild")
def rebuild_paper_docx(paper_id: str, request: PaperRewriteRequest):
    paper = db.get_paper(paper_id)
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found.")
        
    sections = db.get_paper_sections(paper_id)
    references = db.get_paper_references(paper_id)
    
    # Simple layout mapping
    layout_map = {
        "margins": {"top": 1.0, "bottom": 1.0, "left": 1.0, "right": 1.0}
    }
    
    output_filename = f"rebuilt_{paper_id}.docx"
    output_path = os.path.join(settings.OUTPUT_DIR, output_filename)
    
    try:
        rebuild_document(
            sections=sections,
            references=references,
            layout_map=layout_map,
            output_path=output_path,
            journal_format=request.journal_format,
            media_dir=os.path.join(settings.UPLOAD_DIR, "media")
        )
        return {"filename": output_filename, "format": "docx"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to rebuild document: {str(e)}")

@app.get("/api/v1/papers/{paper_id}/download")
def download_rebuilt_file(paper_id: str, file_format: str = Query("docx", enum=["docx", "pdf"])):
    docx_filename = f"rebuilt_{paper_id}.docx"
    docx_path = os.path.join(settings.OUTPUT_DIR, docx_filename)
    
    if not os.path.exists(docx_path):
        raise HTTPException(status_code=404, detail="Rebuilt document not found. Please run rebuild first.")
        
    if file_format == "pdf":
        pdf_filename = f"rebuilt_{paper_id}.pdf"
        pdf_path = os.path.join(settings.OUTPUT_DIR, pdf_filename)
        
        # If PDF already generated, serve it
        if os.path.exists(pdf_path):
            return FileResponse(pdf_path, media_type="application/pdf", filename=f"rebuilt_paper.pdf")
            
        # Try to convert on the fly
        converted = convert_docx_to_pdf(docx_path, pdf_path)
        if converted and os.path.exists(pdf_path):
            return FileResponse(pdf_path, media_type="application/pdf", filename=f"rebuilt_paper.pdf")
        else:
            raise HTTPException(
                status_code=501, 
                detail="PDF conversion engine is not available on this server. Please download the DOCX file."
            )
            
    return FileResponse(docx_path, media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document", filename=f"rebuilt_paper.docx")
