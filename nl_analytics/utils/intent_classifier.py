import re
import logging

logger = logging.getLogger(__name__)

def classify_intent_heuristics(question: str) -> str:
    """
    Classify intent using rule-based heuristics as a fast-path or fallback.
    """
    question_lower = question.lower()
    
    # RAG keywords
    rag_keywords = [
        r'\bpolicy\b', r'\bpolicies\b', r'\bdefinition\b', r'\bdefinitions\b', 
        r'\bguideline\b', r'\bguidelines\b', r'\brule\b', r'\brules\b', 
        r'\bhow to\b', r'\bwhat is\b', r'\bmean\b', r'\bmeaning\b',
        r'\bformula\b', r'\bformulas\b', r'\btarget\b', r'\btargets\b'
    ]
    
    for kw in rag_keywords:
        if re.search(kw, question_lower):
            return "rag"
            
    # Default fallback (most data queries are SQL)
    return "sql"

def classify_intent(question: str, llm_classifier_func=None) -> str:
    """
    Main entry point for intent classification.
    Delegates to the LLM classifier function if available, with a heuristic fallback.
    """
    if llm_classifier_func:
        try:
            intent = llm_classifier_func(question)
            if intent in ["sql", "rag"]:
                return intent
        except Exception as e:
            logger.warning(f"LLM intent classification failed: {e}. Falling back to heuristics.")
            
    return classify_intent_heuristics(question)
