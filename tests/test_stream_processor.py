from src.stream_processor import build_event_stream


def test_build_event_stream_returns_real_time_like_transactions():
    stream = build_event_stream()
    assert len(stream) == 8
    assert all('risk_score' in tx for tx in stream)
    assert all('decision' in tx for tx in stream)
    assert all('event_type' in tx for tx in stream)
    assert all('payment_id' in tx for tx in stream)
    assert all('merchant_id' in tx for tx in stream)
    assert all('amount' in tx for tx in stream)
    assert all('currency' in tx for tx in stream)
    assert all('payment_method' in tx for tx in stream)
    assert all('country' in tx for tx in stream)
    assert all('device_id' in tx for tx in stream)
    assert all('merchant_risk_score' in tx for tx in stream)
    assert all('device_risk' in tx for tx in stream)
    assert all(isinstance(tx['amount'], (int, float)) for tx in stream)
    assert all(tx['amount'] > 0 for tx in stream)
    assert all(tx['currency'] == 'INR' for tx in stream)
