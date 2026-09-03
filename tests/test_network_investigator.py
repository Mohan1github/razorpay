from src.network_investigator import build_network


def test_shared_device_creates_investigation_connection():
    result = build_network([
        {'transaction_id': 'TXN-1', 'customer_id': 'c1', 'customer_name': 'A', 'device_id': 'd1', 'merchant_id': 'm1', 'merchant': 'Shop', 'risk_score': 82, 'decision': 'BLOCK'},
        {'transaction_id': 'TXN-2', 'customer_id': 'c2', 'customer_name': 'B', 'device_id': 'd1', 'merchant_id': 'm2', 'merchant': 'Travel', 'risk_score': 67, 'decision': 'REVIEW'},
    ])

    assert result['summary']['suspicious_clusters'] == 1
    assert any(item['relationship'] == 'shared device' for item in result['connections'])
    assert result['clusters'][0]['highest_risk'] == 82
