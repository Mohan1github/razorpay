from src.database import fetch_recent_transactions, save_transaction


def test_persistence_round_trip():
    sample = {
        'transaction_id': 'TXN-DB-001',
        'customer_name': 'Test User',
        'merchant': 'CloudCart',
        'amount': 2500,
        'risk_score': 62,
        'decision': 'REVIEW',
        'reasons': ['Large transaction amount exceeds the user’s normal spend profile.'],
        'explanation': 'High-risk payment requires manual review.',
    }

    save_transaction(sample)
    rows = fetch_recent_transactions(limit=5)
    assert any(item['transaction_id'] == 'TXN-DB-001' for item in rows)
