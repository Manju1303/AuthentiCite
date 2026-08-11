# backend/app/rewrite/crew_rewriter.py

import os
from typing import Optional
from backend.app.config import settings

def get_crew_llm():
    """
    Constructs a LangChain chat model based on configured settings.
    """
    provider = settings.LLM_PROVIDER.lower()
    
    if provider == "gemini" and settings.GEMINI_API_KEY:
        try:
            from langchain_google_genai import ChatGoogleGenerativeAI
            return ChatGoogleGenerativeAI(
                model=settings.GEMINI_MODEL,
                google_api_key=settings.GEMINI_API_KEY,
                temperature=0.2
            )
        except Exception as e:
            print(f"Could not load LangChain Gemini wrapper: {e}")
            
    if provider == "deepseek" and settings.DEEPSEEK_API_KEY:
        try:
            from langchain_openai import ChatOpenAI
            return ChatOpenAI(
                model=settings.DEEPSEEK_MODEL,
                openai_api_key=settings.DEEPSEEK_API_KEY,
                openai_api_base="https://api.deepseek.com/v1",
                temperature=0.2
            )
        except Exception as e:
            print(f"Could not load LangChain DeepSeek wrapper: {e}")
            
    # Default to Ollama wrapper
    try:
        from langchain_community.chat_models import ChatOllama
        return ChatOllama(
            model=settings.OLLAMA_MODEL,
            base_url=settings.OLLAMA_API_URL,
            temperature=0.2
        )
    except Exception as e:
        print(f"Could not load LangChain Ollama wrapper: {e}")
        return None

def rewrite_text_with_crew(
    text: str,
    context_before: str = "",
    context_after: str = "",
    target_similarity: float = 0.15
) -> Optional[str]:
    """
    Orchestrates a CrewAI Multi-Agent pipeline to rewrite academic text.
    
    - Agent 1 (Researcher): Isolates math equations, LaTeX expressions, and citations [X] to preserve.
    - Agent 2 (Editor): Rewrites the core paragraphs for flow, clarity, and low similarity index.
    - Agent 3 (Reviewer): Peer reviews to verify that no citations or mathematical formulas were lost.
    
    If CrewAI packages are not present in the runtime environment, returns None (graceful fallback).
    """
    try:
        from crewai import Agent, Task, Crew, Process
    except ImportError:
        print("CrewAI is not installed. Falling back to direct single-turn LLM rewriter.")
        return None
        
    llm = get_crew_llm()
    if not llm:
        print("Failed to initialize LangChain model for CrewAI. Falling back.")
        return None
        
    print(f"Initializing CrewAI pipeline using model: {getattr(llm, 'model', 'default')}")
    
    # 1. Define Agents
    researcher = Agent(
        role="Principal Academic Formatting & Structural Analyst",
        goal="Identify, index, and protect all mathematical formulas, LaTeX code, scientific variables, and citation brackets.",
        backstory=(
            "You are a meticulous scholar specializing in academic structure and typesetting standards. Your primary objective "
            "is to catalog citation markers (e.g., [1], [2-5], or (Smith, 2021)) and LaTeX equations/symbols in the target paragraph. "
            "You map their exact positions to guarantee they are never corrupted, altered, or omitted during the editing process."
        ),
        verbose=False,
        allow_delegation=False,
        llm=llm
    )
    
    editor = Agent(
        role="Senior Scientific Copyeditor & Rhetoric Specialist",
        goal="Restructure paragraphs using advanced scientific vocabulary and seamless transitions while reducing similarity scores.",
        backstory=(
            "You are a master of academic rhetoric and English composition. You transform wordy, passive, or repetitive drafts "
            "into crisp, elegant, and precise academic prose. You replace generic words with active scientific verbs, optimize sentence "
            "lengths, and ensure the narrative transitions naturally from the preceding paragraph (Context Before) and into the succeeding "
            "paragraph (Context After). You output ONLY the rewritten paragraph, matching the surrounding tone and pronouns."
        ),
        verbose=False,
        allow_delegation=False,
        llm=llm
    )
    
    reviewer = Agent(
        role="Journal Editor-in-Chief & Peer Review Coordinator",
        goal="Enforce rigorous academic styling, context alignment, and formula/citation preservation on the final draft.",
        backstory=(
            "You are a strict journal editor who ensures that all manuscripts meet the absolute highest standards of clarity, "
            "academic alignment, and formatting accuracy. You verify that the rewritten text transitions smoothly within the "
            "surrounding context, corrects any grammatical shifts, and contains every cataloged citation and mathematical expression "
            "exactly as they appeared in the original text. You output ONLY the final, polished paragraph without markdown wraps or meta-text."
        ),
        verbose=False,
        allow_delegation=False,
        llm=llm
    )
    
    # 2. Define Tasks
    analyze_task = Task(
        description=(
            f"Analyze this target paragraph: '{text}'\n"
            "Identify, list, and note the exact positions of all citation markers, inline/block LaTeX equations, and mathematical variables. "
            "Create a strict protection map for the editor to follow."
        ),
        expected_output="A structured list of citation markers and LaTeX mathematical segments to preserve.",
        agent=researcher
    )
    
    rewrite_task = Task(
        description=(
            f"Rewrite this paragraph to improve academic style and reduce similarity below {target_similarity * 100}%:\n"
            f"'{text}'\n\n"
            f"Surrounding Context to Align with:\n"
            f"- Context Before: '{context_before}'\n"
            f"- Context After: '{context_after}'\n\n"
            "Guidelines:\n"
            "1. Use active, robust scientific vocabulary. Avoid passive voice, conversational phrasing, or generic verbs.\n"
            "2. Ensure the text flows seamlessly between the 'Context Before' and 'Context After' paragraphs (match tenses, pronouns, and narrative tone).\n"
            "3. Reference the protected elements list from the researcher to keep all citations and equations perfectly intact."
        ),
        expected_output="The rewritten paragraph text only. Do not add markdown blocks, comments, or quotes.",
        agent=editor
    )
    
    review_task = Task(
        description=(
            f"Conduct a peer review of the rewritten paragraph against the original paragraph: '{text}'.\n"
            "Check for:\n"
            "1. Absolute preservation of all original citation brackets and LaTeX formulas.\n"
            "2. Logical and seamless transitions with the surrounding context (Before: '{context_before}' | After: '{context_after}').\n"
            "3. Refined academic tone, vocabulary density, and active voice.\n\n"
            "If any citation, formula, or transition transition is compromised, restore it. Output ONLY the raw paragraph text."
        ),
        expected_output="The final polished paragraph text. No markdown backticks, conversational introductions, or summary notes."
        ,agent=reviewer
    )
    
    # 3. Assemble and Kickoff Crew
    crew = Crew(
        agents=[researcher, editor, reviewer],
        tasks=[analyze_task, rewrite_task, review_task],
        process=Process.sequential,
        verbose=False
    )
    
    try:
        result = crew.kickoff()
        # Clean up any potential markdown wraps in output
        result_str = str(result).strip()
        if result_str.startswith("```") and result_str.endswith("```"):
            result_str = result_str.strip("`").strip()
            if result_str.startswith("text\n") or result_str.startswith("plaintext\n"):
                result_str = "\n".join(result_str.split("\n")[1:])
        return result_str
    except Exception as e:
        print(f"CrewAI execution failed: {e}")
        return None
