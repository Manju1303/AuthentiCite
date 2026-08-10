import httpx
import json
from typing import Dict, Any, Optional
from backend.app.config import settings

def rewrite_text(
    text: str, 
    context_before: str = "", 
    context_after: str = "", 
    target_similarity: float = 0.15
) -> str:
    """
    Rewrites academic text using the selected LLM provider.
    Context is provided to maintain formatting, equations, flow, and citation keys.
    """
    # System prompt to guide the rewriter
    system_instruction = (
        "You are an expert academic paper editor. Your task is to rewrite the input paragraph to reduce plagiarism/similarity "
        f"and improve academic tone, aiming for a similarity index below {target_similarity * 100}%. "
        "Adhere to the following rules:\n"
        "1. PRESERVE ALL CITATIONS EXACTLY. Do not modify or remove any citation brackets like [1], [2-5], or (Smith, 2021).\n"
        "2. PRESERVE MATH EQUATIONS AND FORMULAS EXACTLY. Do not touch LaTeX blocks, subscripts, or mathematical expressions.\n"
        "3. MAINTAIN MEANING: Do not hallucinate or change facts, numbers, or findings.\n"
        "4. ACADEMIC TONE: Use formal, precise, and concise scientific vocabulary. Improve flow and readability.\n"
        "5. ONLY return the rewritten paragraph text. Do NOT add conversational padding, warnings, explanations, or quotes."
    )
    
    prompt = f"System Rules:\n{system_instruction}\n\n"
    if context_before:
        prompt += f"Context Before (DO NOT REWRITE THIS):\n{context_before}\n\n"
    prompt += f"Paragraph to Rewrite:\n{text}\n\n"
    if context_after:
        prompt += f"Context After (DO NOT REWRITE THIS):\n{context_after}\n\n"
    prompt += "Rewritten Paragraph:"

    # Check if CrewAI multi-agent rewrite should be used
    if getattr(settings, "USE_CREWAI", False):
        try:
            from backend.app.rewrite.crew_rewriter import rewrite_text_with_crew
            crew_result = rewrite_text_with_crew(
                text=text,
                context_before=context_before,
                context_after=context_after,
                target_similarity=target_similarity
            )
            if crew_result:
                return crew_result
        except Exception as e:
            print(f"CrewAI routing failed: {e}. Falling back to single-turn LLM.")

    provider = settings.LLM_PROVIDER.lower()
    
    if provider == "gemini" and settings.GEMINI_API_KEY:
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={settings.GEMINI_API_KEY}"
            headers = {"Content-Type": "application/json"}
            payload = {
                "contents": [
                    {
                        "parts": [
                            {"text": prompt}
                        ]
                    }
                ],
                "generationConfig": {
                    "temperature": 0.2,
                    "maxOutputTokens": 1024
                }
            }
            response = httpx.post(url, headers=headers, json=payload, timeout=60.0)
            response.raise_for_status()
            res_json = response.json()
            rewritten = res_json["candidates"][0]["content"]["parts"][0]["text"].strip()
            # Clean up potential markdown formatting wrapping the output
            if rewritten.startswith("```") and rewritten.endswith("```"):
                rewritten = rewritten.strip("`").strip()
                if rewritten.startswith("text\n") or rewritten.startswith("plaintext\n"):
                    rewritten = "\n".join(rewritten.split("\n")[1:])
            return rewritten
        except Exception as e:
            print(f"Gemini API Error: {e}")
            # Fallback to Ollama or simple editing if failure occurs
            
    if provider == "deepseek" and settings.DEEPSEEK_API_KEY:
        try:
            url = "https://api.deepseek.com/v1/chat/completions"
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {settings.DEEPSEEK_API_KEY}"
            }
            payload = {
                "model": "deepseek-chat",
                "messages": [
                    {"role": "system", "content": system_instruction},
                    {"role": "user", "content": f"Please rewrite this paragraph:\n{text}"}
                ],
                "temperature": 0.2,
                "max_tokens": 1024
            }
            response = httpx.post(url, headers=headers, json=payload, timeout=60.0)
            response.raise_for_status()
            res_json = response.json()
            return res_json["choices"][0]["message"]["content"].strip()
        except Exception as e:
            print(f"DeepSeek API Error: {e}")
            
    if (provider == "claude" or provider == "anthropic") and settings.ANTHROPIC_API_KEY:
        try:
            url = "https://api.anthropic.com/v1/messages"
            headers = {
                "x-api-key": settings.ANTHROPIC_API_KEY,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json"
            }
            payload = {
                "model": settings.CLAUDE_MODEL,
                "max_tokens": settings.MAX_TOKENS,
                "system": system_instruction,
                "messages": [
                    {"role": "user", "content": f"Context before: {context_before}\nRewrite: {text}\nContext after: {context_after}"}
                ],
                "temperature": 0.2
            }
            response = httpx.post(url, headers=headers, json=payload, timeout=60.0)
            response.raise_for_status()
            res_json = response.json()
            return res_json["content"][0]["text"].strip()
        except Exception as e:
            print(f"Claude API Error: {e}")
            
    # Default to Ollama (local host)
    try:
        url = f"{settings.OLLAMA_API_URL}/api/chat"
        payload = {
            "model": settings.OLLAMA_MODEL,
            "messages": [
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": f"Context before: {context_before}\nRewrite: {text}\nContext after: {context_after}"}
            ],
            "stream": False,
            "options": {
                "temperature": 0.2
            }
        }
        response = httpx.post(url, json=payload, timeout=60.0)
        response.raise_for_status()
        res_json = response.json()
        return res_json["message"]["content"].strip()
    except Exception as e:
        print(f"Ollama local error: {e}")
        # In case all providers fail, do a minor programmatic transform (fallback)
        return f"[Rewritten Fallback] {text}"
