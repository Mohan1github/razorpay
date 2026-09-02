from src.stream_processor import build_event_stream


def test_build_event_stream_returns_real_time_like_transactions():
    stream = build_event_stream()
    assert len(stream) == 8
    assert all('risk_score' in tx for tx in stream)
    assert all('decision' in tx for tx in stream)
    assert all('event_type' in tx for tx in stream)
