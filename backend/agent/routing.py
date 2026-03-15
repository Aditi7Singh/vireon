"""Query router and classifier for CFO agent.

Routes user queries to appropriate LLM mode (fast vs thinking) while minimizing API calls.
Uses keyword pre-filtering before expensive LLM classification.
"""

from typing import Literal
import logging

from backend.agent.prompts import build_query_classifier_prompt

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Query type definitions
QueryType = Literal["simple", "complex", "alert"]

# Keyword pre-filters (lowercase, no punctuation)
SIMPLE_KEYWORDS = [
    "balance", "cash", "burn rate", "burn", "mrr", "arr", 
    "runway", "how much", "what is", "current", "show me",
    "get", "fetch", "list", "total", "amount", "growth rate",
]

COMPLEX_KEYWORDS = [
    "why", "what if", "hire", "scenario", "forecast", "should we",
    "impact", "reduce", "increase", "explain", "analyze",
    "compare", "trend analysis", "project", "simulate",
    "plan", "strategy", "decision", "option", "alternative",
]

ALERT_KEYWORDS = [
    "spike", "anomaly", "alert", "unusual", "surprised", "unexpected",
    "double", "duplicate", "red flag", "critical",
    "warning", "risk", "concerning", "problem", "issue",
]


def _normalize_query(query: str) -> str:
    """Normalize query for keyword matching."""
    return query.lower().strip()


def _contains_keyword(query: str, keywords: list) -> bool:
    """Check if query contains any keyword (substring match)."""
    normalized = _normalize_query(query)
    for keyword in keywords:
        if keyword in normalized:
            return True
    return False


def classify_query(user_message: str) -> QueryType:
    """
    Classify a user query into one of three types: simple, complex, alert.
    
    Uses keyword pre-filtering first to avoid expensive LLM calls:
    1. If message matches ALERT keywords → return "alert" (no LLM call)
    2. If message matches COMPLEX keywords → return "complex" (no LLM call)
    3. If message matches SIMPLE keywords AND no complex/alert → return "simple"
    4. Otherwise → call LLM classifier for borderline cases
    
    Args:
        user_message: The user's natural language query
    
    Returns:
        Query type: "simple", "complex", or "alert"
    """
    # Step 1: Check for ALERT keywords (highest priority)
    if _contains_keyword(user_message, ALERT_KEYWORDS):
        query_type = "alert"
        logger.info(f"[ROUTER] Query type: {query_type} (via ALERT keyword pre-filter)")
        return query_type
    
    # Step 2: Check for COMPLEX keywords
    if _contains_keyword(user_message, COMPLEX_KEYWORDS):
        query_type = "complex"
        logger.info(f"[ROUTER] Query type: {query_type} (via COMPLEX keyword pre-filter)")
        return query_type
    
    # Step 3: Check for SIMPLE keywords (only if no complex/alert matched)
    if _contains_keyword(user_message, SIMPLE_KEYWORDS):
        query_type = "simple"
        logger.info(f"[ROUTER] Query type: {query_type} (via SIMPLE keyword pre-filter)")
        return query_type
    
    # Step 4: Fall back to LLM classifier for ambiguous queries
    query_type = _classify_with_llm(user_message)
    logger.info(f"[ROUTER] Query type: {query_type} (via LLM classifier)")
    return query_type


def _classify_with_llm(user_message: str) -> QueryType:
    """
    Use LLM to classify a query when keywords don't match.
    
    Args:
        user_message: The user's query
    
    Returns:
        Query type as classified by LLM
    """
    try:
        # Import here to avoid circular imports and handle missing LLM gracefully
        from langchain_groq import ChatGroq
        from backend.config.settings import Settings
        
        # Initialize Groq LLM (fast mode for classification)
        llm = ChatGroq(
            model=Settings.GROQ_FAST_MODEL,
            temperature=0,  # Deterministic
            api_key=Settings.GROQ_API_KEY,
        )
        
        # Get the classification prompt
        classifier_prompt = build_query_classifier_prompt(user_message)
        
        # Call the LLM
        response = llm.invoke(classifier_prompt)
        response_text = response.content.strip().lower()
        
        # Parse the response (expecting one word: simple, complex, or alert)
        if "simple" in response_text:
            return "simple"
        elif "complex" in response_text:
            return "complex"
        elif "alert" in response_text:
            return "alert"
        else:
            # Fallback to complex if we can't parse (safer to over-think)
            logger.warning(f"[ROUTER] Could not parse LLM response: {response_text}. Defaulting to 'complex'.")
            return "complex"
    
    except Exception as e:
        # If LLM call fails, default to complex (safer)
        logger.error(f"[ROUTER] LLM classification failed: {str(e)}. Defaulting to 'complex'.")
        return "complex"


def should_use_thinking_mode(query_type: QueryType) -> bool:
    """
    Determine if thinking mode should be used for this query type.
    
    Thinking mode (QwQ-32B) uses more tokens and is slower, so we only use it for complex queries.
    
    Args:
        query_type: The classified query type
    
    Returns:
        True if thinking mode should be used (complex queries only)
    """
    use_thinking = query_type == "complex"
    logger.info(f"[ROUTER] Thinking mode: {use_thinking}")
    return use_thinking


def get_routing_decision(user_message: str) -> dict:
    """
    Get the complete routing decision for a query.
    
    Args:
        user_message: The user's query
    
    Returns:
        Dictionary with routing info: {query_type, use_thinking, model_name}
    """
    query_type = classify_query(user_message)
    use_thinking = should_use_thinking_mode(query_type)
    
    # Determine which model to use
    if use_thinking:
        model_name = "qwq-32b"  # Thinking mode
    else:
        model_name = "qwen2-32b"  # Fast mode
    
    decision = {
        "query_type": query_type,
        "use_thinking": use_thinking,
        "model_name": model_name,
        "message": user_message[:80] + ("..." if len(user_message) > 80 else ""),
    }
    
    logger.info(f"[ROUTER] Full decision: {decision}")
    return decision


if __name__ == "__main__":
    # Test cases
    print("Query Routing Tests")
    print("=" * 70)
    
    test_cases = [
        ("What is our current cash balance?", "simple"),
        ("What happens if we hire 3 engineers next month?", "complex"),
        ("Why did AWS costs spike last month?", "alert"),
        ("What is our MRR growth rate?", "simple"),
        ("Should we raise prices to extend runway?", "complex"),
    ]
    
    all_passed = True
    
    for query, expected in test_cases:
        result = classify_query(query)
        status = "PASS" if result == expected else "FAIL"
        
        if result != expected:
            all_passed = False
        
        print(f"\n{status}: '{query}'")
        print(f"  Expected: {expected}")
        print(f"  Got:      {result}")
    
    print("\n" + "=" * 70)
    
    if all_passed:
        print("All tests PASSED")
    else:
        print("Some tests FAILED")
    
    # Show routing decision for one example
    print("\n" + "=" * 70)
    print("Example routing decision:")
    decision = get_routing_decision("What happens if we hire 5 engineers?")
    for key, value in decision.items():
        print(f"  {key}: {value}")

