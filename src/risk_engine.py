from __future__ import annotations

from src.llm_explainer import generate_risk_explanation


def _rule_based_score(tx: dict) -> tuple[int, list[str]]:
    score = 0
    reasons = []

    amount = float(tx.get('amount', 0))
    merchant_risk_score = float(tx.get('merchant_risk_score', 0))
    device_risk = float(tx.get('device_risk', 0))
    velocity = int(tx.get('velocity', 0))
    hour = int(tx.get('transaction_hour', 12))
    failure_count = int(tx.get('failure_count', 0))
    is_new_customer = bool(tx.get('is_new_customer', False))
    historical_chargebacks = int(tx.get('historical_chargebacks', 0))
    country_mismatch = bool(tx.get('country_mismatch', False))

    if amount > 5000:
        score += 20
        reasons.append('Large transaction amount exceeds the user’s normal spend profile.')
    if merchant_risk_score > 0.7:
        score += 25
        reasons.append('Merchant risk score is elevated for this payment channel.')
    if device_risk > 0.7:
        score += 18
        reasons.append('Device fingerprint matches patterns previously linked to suspicious activity.')
    if velocity > 5:
        score += 12
        reasons.append('Payment velocity is unusually high for the customer profile.')
    if 0 <= hour <= 4:
        score += 8
        reasons.append('Transaction occurs in a risky late-night window.')
    if failure_count >= 2:
        score += 10
        reasons.append('Repeated failures suggest automated retries or malicious intent.')
    if is_new_customer:
        score += 8
        reasons.append('New customer has no established trust history.')
    if historical_chargebacks >= 3:
        score += 15
        reasons.append('Customer has a charged-back history that increases exposure.')
    if country_mismatch:
        score += 10
        reasons.append('Location mismatch between customer profile and transaction origin.')

    if amount > 15000 and historical_chargebacks >= 2:
        score += 10
        reasons.append('High-dollar payment combined with previous chargebacks indicates elevated merchant risk.')

    score = max(0, min(100, score))
    return score, reasons[:4] if reasons else ['No major risk signals detected.']


def _model_score(tx: dict) -> int:
    amount = float(tx.get('amount', 0))
    merchant_risk_score = float(tx.get('merchant_risk_score', 0))
    device_risk = float(tx.get('device_risk', 0))
    velocity = int(tx.get('velocity', 0))
    failure_count = int(tx.get('failure_count', 0))
    historical_chargebacks = int(tx.get('historical_chargebacks', 0))
    is_new_customer = bool(tx.get('is_new_customer', False))
    country_mismatch = bool(tx.get('country_mismatch', False))

    weighted = 0.0
    weighted += min(30.0, (amount / 20000.0) * 30.0)
    weighted += merchant_risk_score * 25.0
    weighted += device_risk * 25.0
    weighted += min(15.0, velocity * 2.5)
    weighted += min(12.0, failure_count * 6.0)
    weighted += historical_chargebacks * 7.0
    weighted += 8.0 if is_new_customer else 0.0
    weighted += 10.0 if country_mismatch else 0.0

    model_score = min(100, round(weighted))
    return model_score


def _make_explanation(reasons: list[str], risk_score: int, decision: str) -> str:
    return generate_risk_explanation(reasons, risk_score, decision)


def score_transaction(tx: dict) -> dict:
    """Score a payment transaction with a hybrid risk engine.

    This combines a deterministic rule engine with a model-like confidence layer
    and produces an analyst-friendly explanation.
    """
    rule_score, reasons = _rule_based_score(tx)
    model_score = _model_score(tx)
    combined_score = round((rule_score * 0.65) + (model_score * 0.35))
    final_score = max(0, min(100, combined_score))

    if final_score >= 75:
        decision = 'BLOCK'
    elif final_score >= 45:
        decision = 'REVIEW'
    else:
        decision = 'APPROVE'

    explanation = _make_explanation(reasons, final_score, decision)

    return {
        'risk_score': final_score,
        'model_score': model_score,
        'decision': decision,
        'reasons': reasons,
        'explanation': explanation,
    }


def generate_demo_transactions() -> list[dict]:
    base = [
        {
            'transaction_id': 'TXN-1001',
            'customer_name': 'Aarav Mehta',
            'merchant': 'CloudCart',
            'amount': 3200,
            'merchant_risk_score': 0.25,
            'device_risk': 0.18,
            'velocity': 2,
            'transaction_hour': 14,
            'failure_count': 0,
            'is_new_customer': False,
            'historical_chargebacks': 0,
            'country_mismatch': False,
            'source': 'payment-gateway',
            'event_type': 'payment_event',
        },
        {
            'transaction_id': 'TXN-1002',
            'customer_name': 'Priya Nair',
            'merchant': 'TravelPrime',
            'amount': 7800,
            'merchant_risk_score': 0.82,
            'device_risk': 0.78,
            'velocity': 7,
            'transaction_hour': 2,
            'failure_count': 3,
            'is_new_customer': True,
            'historical_chargebacks': 4,
            'country_mismatch': True,
            'source': 'payment-gateway',
            'event_type': 'payment_event',
        },
        {
            'transaction_id': 'TXN-1003',
            'customer_name': 'Karan Shah',
            'merchant': 'GroceryHub',
            'amount': 1490,
            'merchant_risk_score': 0.42,
            'device_risk': 0.31,
            'velocity': 1,
            'transaction_hour': 17,
            'failure_count': 0,
            'is_new_customer': False,
            'historical_chargebacks': 1,
            'country_mismatch': False,
            'source': 'payment-gateway',
            'event_type': 'payment_event',
        },
        {
            'transaction_id': 'TXN-1004',
            'customer_name': 'Neha Verma',
            'merchant': 'ZestPay',
            'amount': 22000,
            'merchant_risk_score': 0.66,
            'device_risk': 0.56,
            'velocity': 5,
            'transaction_hour': 23,
            'failure_count': 1,
            'is_new_customer': True,
            'historical_chargebacks': 2,
            'country_mismatch': True,
            'source': 'payment-gateway',
            'event_type': 'payment_event',
        },
    ]

    return base


def summarize_decision_summary(transactions: list[dict]) -> dict:
    approved = sum(1 for tx in transactions if tx.get('decision') == 'APPROVE')
    review = sum(1 for tx in transactions if tx.get('decision') == 'REVIEW')
    blocked = sum(1 for tx in transactions if tx.get('decision') == 'BLOCK')
    average = round(sum(tx.get('risk_score', 0) for tx in transactions) / max(len(transactions), 1), 1)

    return {
        'approved': approved,
        'review': review,
        'blocked': blocked,
        'average_risk_score': average,
    }
