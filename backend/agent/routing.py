"""
Query Router
==========
Routes user queries to simple/complex/alert classification.
Uses keyword pre-filter for fast routing, LLM for edge cases.
"""

from typing import Literal
from config.settings import get_fast_llm
from agent.prompts import build_query_classifier_prompt


# Keyword sets for fast pre-filtering
SIMPLE_KEYWORDS = {"balance", "cash", "burn rate", "mrr", "arr", "runway", "how much", "what is", 
                  "depreciation", "assets", "book value", "loans", "debt", "payroll", "taxes", 
                                    "tax liability", "fixed assets", "asset utilization", "invoice status", "approval status",
                                    "close status", "budget utilization", "bank reconciliation"}
COMPLEX_KEYWORDS = {"why", "what if", "hire", "scenario", "forecast", "should we", "impact", 
                   "reduce", "increase", "explain", "what happens", "simulate", "cut",
                   "depreciation schedule", "loan impact", "tax planning", "payroll optimization",
                                     "asset management", "debt reduction", "capital efficiency", "month-end close",
                                     "consolidation", "multi-entity", "period lock", "reallocation", "approval workflow",
                                     "collections strategy", "vendor optimization", "payment run"}
ALERT_KEYWORDS = {"spike", "anomaly", "alert", "unusual", "surprised", "unexpected", 
                 "double", "duplicate", "weird", "odd", "suspicious", "overdue", "breach",
                                 "tax deadline", "loan covenant", "asset impairment", "close blocked", "reconciliation failed",
                                 "approval stuck", "budget overrun"}


def classify_query(user_message: str) -> Literal["simple", "complex", "alert"]:
    """
    Classify a user query as simple, complex, or alert.
    
    Uses keyword pre-filter first to avoid unnecessary LLM calls,
    then falls back to LLM classification for edge cases.
    
    Args:
        user_message: The user's input message
        
    Returns:
        Query type: "simple", "complex", or "alert"
    """
    message_lower = user_message.lower()
    
    # Keyword pre-filter
    if any(kw in message_lower for kw in ALERT_KEYWORDS):
        print(f"[ROUTER] Query type: alert (keyword match)")
        return "alert"
    
    if any(kw in message_lower for kw in COMPLEX_KEYWORDS):
        print(f"[ROUTER] Query type: complex (keyword match)")
        return "complex"
    
    if any(kw in message_lower for kw in SIMPLE_KEYWORDS):
        print(f"[ROUTER] Query type: simple (keyword match)")
        return "simple"
    
    # Fallback to LLM classification for ambiguous queries
    try:
        llm = get_fast_llm()
        prompt = build_query_classifier_prompt(user_message)
        response = llm.invoke(prompt)
        result = response.content.strip().lower()
        
        if result in ("simple", "complex", "alert"):
            print(f"[ROUTER] Query type: {result} (LLM classification)")
            return result
    except Exception as e:
        print(f"[ROUTER] LLM classification failed: {e}")
    
    # Default to complex (safer to over-think than under-think)
    print(f"[ROUTER] Query type: complex (default)")
    return "complex"


def should_use_thinking_mode(query_type: str) -> bool:
    """
    Determine if thinking mode should be used for a query type.
    
    Thinking mode uses more tokens (QwQ-32B) but provides better
    reasoning for complex multi-step queries.
    
    Args:
        query_type: The classified query type
        
    Returns:
        True if thinking mode should be used
    """
    return query_type == "complex"


# Test queries
if __name__ == "__main__":
    test_queries = [
        "What is our current cash balance?",
        "What happens if we hire 3 engineers next month?",
        "Why did AWS costs spike last month?",
        "What is our MRR growth rate?",
        "Should we raise prices to extend runway?"
    ]
    
    print("Query Classification Tests")
    print("=" * 60)
    
    for query in test_queries:
        query_type = classify_query(query)
        thinking = should_use_thinking_mode(query_type)
        print(f"\nQuery: {query}")
        print(f"Type: {query_type} | Thinking: {thinking}")
