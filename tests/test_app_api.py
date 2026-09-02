import json

from app import app


def test_risk_score_api_returns_processed_transaction():
    client = app.test_client()
    payload = {
        'amount': 12000,
        'merchant_risk_score': 0.82,
        'device_risk': 0.72,
        'velocity': 7,
        'transaction_hour': 2,
        'failure_count': 2,
        'is_new_customer': True,
        'historical_chargebacks': 3,
        'country_mismatch': True,
        'customer_name': 'Sam Patel',
        'merchant': 'SkyCart',
    }

    response = client.post('/api/risk/score', data=json.dumps(payload), content_type='application/json')
    assert response.status_code == 200
    body = response.get_json()
    assert 'risk_score' in body
    assert 'decision' in body
    assert body['decision'] in {'APPROVE', 'REVIEW', 'BLOCK'}
