from src.llm_explainer import generate_risk_explanation


def test_generate_risk_explanation_returns_string_without_llm_key():
    result = generate_risk_explanation(
        ['Large transaction amount exceeds the user’s normal spend profile.', 'Repeated failures suggest automated retries or malicious intent.'],
        82,
        'BLOCK',
    )
    assert isinstance(result, str)
    assert len(result) > 20
