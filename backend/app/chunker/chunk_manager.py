from typing import List, Dict, Any

def get_paragraph_with_context(sections: List[Dict[str, Any]], target_index: int) -> Dict[str, Any]:
    """
    Returns the target paragraph text along with preceding and succeeding paragraphs 
    for context, ensuring the LLM is aware of the flow and surrounding citations.
    """
    target = sections[target_index]
    if target["layout_metadata"].get("type") in ["image", "table"]:
        return {
            "text": target["original_text"],
            "context_before": "",
            "context_after": "",
            "section_name": target["section_name"]
        }
        
    context_before = []
    # Fetch up to 2 preceding paragraphs in the same section
    for i in range(max(0, target_index - 2), target_index):
        if sections[i]["section_name"] == target["section_name"] and sections[i]["layout_metadata"].get("type") == "paragraph":
            context_before.append(sections[i]["original_text"])
            
    context_after = []
    # Fetch 1 succeeding paragraph in the same section
    if target_index + 1 < len(sections):
        next_sec = sections[target_index + 1]
        if next_sec["section_name"] == target["section_name"] and next_sec["layout_metadata"].get("type") == "paragraph":
            context_after.append(next_sec["original_text"])
            
    return {
        "text": target["original_text"],
        "context_before": " ".join(context_before),
        "context_after": " ".join(context_after),
        "section_name": target["section_name"]
    }

def chunk_sections_for_similarity(sections: List[Dict[str, Any]], target_words: int = 800) -> List[Dict[str, Any]]:
    """
    Groups paragraphs within the same section into chunks of ~target_words.
    Used for vector database indexing and similarity checks.
    """
    chunks = []
    current_chunk = []
    current_word_count = 0
    chunk_index = 0
    
    for sec in sections:
        if sec["layout_metadata"].get("type") != "paragraph":
            continue
            
        text = sec["original_text"]
        words = text.split()
        word_count = len(words)
        
        # If adding this paragraph exceeds target words and we already have text, save current chunk
        if current_word_count + word_count > target_words and current_chunk:
            chunks.append({
                "chunk_id": f"chunk_{chunk_index}",
                "section_name": current_chunk[0]["section_name"],
                "text": " ".join([c["original_text"] for c in current_chunk]),
                "source_blocks": [c["id"] for c in current_chunk]
            })
            chunk_index += 1
            current_chunk = []
            current_word_count = 0
            
        current_chunk.append(sec)
        current_word_count += word_count
        
    if current_chunk:
        chunks.append({
            "chunk_id": f"chunk_{chunk_index}",
            "section_name": current_chunk[0]["section_name"],
            "text": " ".join([c["original_text"] for c in current_chunk]),
            "source_blocks": [c["id"] for c in current_chunk]
        })
        
    return chunks
