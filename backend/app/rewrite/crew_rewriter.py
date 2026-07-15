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
                model="gemini-2.5-flash",
                google_api_key=settings.GEMINI_API_KEY,
                temperature=0.2
            )
        except Exception as e:
            print(f"Could not load LangChain Gemini wrapper: {e}")
            
    if provider == "deepseek" and settings.DEEPSEEK_API_KEY:
        try:
            from langchain_openai import ChatOpenAI
            return ChatOpenAI(
                model="deepseek-chat",
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
        role="Senior Academic Research Scholar",
        goal="Identify and preserve formulas, citations, and critical facts in the paragraph.",
        backstory=(
            "You are an expert in academic formatting. Your primary job is to extract citation brackets "
            "like [1], [2-5], (Smith, 2021) and LaTeX math expressions, ensuring they are highlighted "
            "and preserved in their exact original form."
        ),
        verbose=False,
        allow_delegation=False,
        llm=llm
    )
    
    editor = Agent(
        role="Professional Scientific Copyeditor",
        goal="Rewrite text blocks in an elegant academic tone while removing similarity patterns.",
        backstory=(
            "You are a master of academic composition. You restructure sentences, vary vocabulary, and "
            "re-order thoughts to ensure zero plagiarism. You use the provided context to ensure transitions "
            "flow seamlessly, but you ONLY output the rewritten paragraph."
        ),
        verbose=False,
        allow_delegation=False,
        llm=llm
    )
    
    reviewer = Agent(
        role="Journal Peer Reviewer",
        goal="Verify that the rewritten paragraph is factual, academically sound, and preserves all original citations/formulas.",
        backstory=(
            "You are a meticulous reviewer. You compare the final rewrite against the original text. "
            "If any citation key or mathematical formula was altered or omitted, you inject it back "
            "in place. You output ONLY the final rewritten paragraph text."
        ),
        verbose=False,
        allow_delegation=False,
        llm=llm
    )
    
    # 2. Define Tasks
    analyze_task = Task(
        description=(
            f"Analyze this paragraph: '{text}'\n"
            "List all citation brackets and LaTeX math equations that must remain completely unchanged."
        ),
        expected_output="A list of citations and equations to preserve.",
        agent=researcher
    )
    
    rewrite_task = Task(
        description=(
            f"Rewrite the input paragraph: '{text}'\n"
            "Aim to reduce plagiarism below {target_similarity * 100}%. Make sentences formal and concise.\n"
            f"Context Before: '{context_before}'\n"
            f"Context After: '{context_after}'\n"
            "Use Researcher list to preserve all citations and equations exactly."
        ),
        expected_output="The rewritten paragraph text only. Do not wrap in markdown or add commentary.",
        agent=editor
    )
    
    review_task = Task(
        description=(
            f"Review this draft against the original paragraph: '{text}'.\n"
            "Verify all citations [1] and math equations are intact. Correct any formatting mistakes.\n"
            "Output ONLY the final, polished paragraph. No commentary, markdown backticks, or intro padding."
        ),
        expected_output="The final polished paragraph text.",
        agent=reviewer
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
