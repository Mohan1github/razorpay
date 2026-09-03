from src.risk_agent import run_riskops_agent


def test_agent_recommends_restriction_for_critical_shared_device():
    transactions = [
        {
            'transaction_id': 'TXN-1', 'customer_id': 'c1', 'customer_name': 'A',
            'device_id': 'dev-1', 'merchant_id': 'm1', 'merchant': 'Shop A',
            'risk_score': 92, 'decision': 'BLOCK',
        },
        {
            'transaction_id': 'TXN-2', 'customer_id': 'c2', 'customer_name': 'B',
            'device_id': 'dev-1', 'merchant_id': 'm2', 'merchant': 'Shop B',
            'risk_score': 84, 'decision': 'BLOCK',
        },
    ]

    result = run_riskops_agent(transactions)

    assert result['priority'] == 'CRITICAL'
    assert result['recommendation'] == 'BLOCK_DEVICE'
    assert result['human_approval_required'] is True
    assert result['confidence'] >= 90
