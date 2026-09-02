from app import app


def test_analytics_endpoint_returns_dashboard_data():
    client = app.test_client()
    response = client.get('/api/analytics')
    assert response.status_code == 200
    payload = response.get_json()
    assert 'decision_mix' in payload
    assert 'risk_trend' in payload
    assert 'merchant_watchlist' in payload
