from __future__ import annotations

import json
import os
from typing import Any
from urllib import error, request


FALLBACK_EXPLANATION = (
    'This payment has elevated risk due to multiple suspicious indicators. '
    'The policy engine identified high-risk transaction patterns and recommends '
    'manual review or blocking based on the current decision.'
)


def _fallback_explanation(reasons: list[str], risk_score: int, decision: str) -> str:
    if not reasons:
        return FALLBACK_EXPLANATION

    primary = reasons[0]
    if decision == 'BLOCK':
        action = 'The system should block this payment pending further verification.'
    elif decision == 'REVIEW':
        action = 'The system should route this payment to a manual review queue.'
    else:
        action = 'The system can approve this payment with normal monitoring.'

    return f'{primary} {action} Current risk score: {risk_score}/100.'


def generate_risk_explanation(reasons: list[str], risk_score: int, decision: str) -> str:
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        return _fallback_explanation(reasons, risk_score, decision)

    prompt = (
        'You are a fintech fraud analyst. Write a concise, production-ready explanation '
        'for this payment decision. Keep it clear and professional. '
        f'Reasons: {reasons}. Decision: {decision}. Risk score: {risk_score}.'
    )

    payload = {
        'model': 'gpt-4o-mini',
        'messages': [
            {'role': 'system', 'content': 'You are a helpful fraud risk analyst.'},
            {'role': 'user', 'content': prompt},
        ],
        'temperature': 0.2,
        'max_tokens': 180,
    }

    req = request.Request(
        'https://api.openai.com/v1/chat/completions',
        data=json.dumps(payload).encode('utf-8'),
        headers={
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {api_key}',
        },
        method='POST',
    )

    try:
        with request.urlopen(req, timeout=10) as response:
            body = response.read().decode('utf-8')
            parsed = json.loads(body)
            text = parsed['choices'][0]['message']['content']
            if isinstance(text, str) and text.strip():
                return text.strip()
    except (error.URLError, error.HTTPError, KeyError, json.JSONDecodeError, ValueError):
        pass

    return _fallback_explanation(reasons, risk_score, decision)
