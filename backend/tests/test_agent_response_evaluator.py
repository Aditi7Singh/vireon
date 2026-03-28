from agent.evaluation import evaluate_agent_response


def test_evaluator_passes_actionable_finance_response():
    result = evaluate_agent_response(
        user_query="What is our cash runway and what should we do?",
        response=(
            "Cash runway is 8.4 months based on current net burn of $52,300/month. "
            "Runway decreased 1.1 months vs last month. Recommended actions: "
            "reduce cloud spend by 12% and defer 1 non-critical hire."
        ),
        required_keywords=["runway", "recommended actions"],
        min_numeric_tokens=2,
        min_score=0.8,
    )

    assert result.passed is True
    assert result.score >= 0.8
    assert result.checks["required_keywords"] is True


def test_evaluator_fails_when_numeric_grounding_missing():
    result = evaluate_agent_response(
        user_query="How is our burn trend?",
        response="Burn is improving and looks healthy. We should keep monitoring.",
        required_keywords=["burn"],
        min_numeric_tokens=2,
        min_score=0.75,
    )

    assert result.passed is False
    assert result.checks["numeric_grounding"] is False


def test_evaluator_flags_weak_confidence_phrasing():
    result = evaluate_agent_response(
        user_query="What is our revenue risk?",
        response=(
            "I think revenue might be okay, maybe there is some upside. "
            "Probably we should wait."
        ),
        required_keywords=["revenue"],
        min_numeric_tokens=0,
        min_score=0.7,
    )

    assert result.passed is False
    assert result.checks["forbidden_phrases"] is False
    assert any("weak-confidence" in item.lower() for item in result.feedback)
