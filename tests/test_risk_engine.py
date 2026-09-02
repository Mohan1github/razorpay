import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.risk_engine import score_transaction


def test_score_transaction_returns_risk_and_reasons():
    tx = {
        'amount': 7200,
        'merchant_risk_score': 0.9,
        'device_risk': 0.85,
        'velocity': 8,
        'transaction_hour': 2,
        'failure_count': 3,
        'is_new_customer': True,
        'historical_chargebacks': 4,
        'country_mismatch': True,
    }

    result = score_transaction(tx)
    assert result['risk_score'] >= 0
    assert result['risk_score'] <= 100
    assert len(result['reasons']) >= 1
    assert result['decision'] in {'APPROVE', 'REVIEW', 'BLOCK'}


def test_score_transaction_has_hybrid_reasoning_fields():
    tx = {
        'amount': 12000,
        'merchant_risk_score': 0.82,
        'device_risk': 0.76,
        'velocity': 6,
        'transaction_hour': 1,
        'failure_count': 2,
        'is_new_customer': True,
        'historical_chargebacks': 3,
        'country_mismatch': True,
    }

    result = score_transaction(tx)
    assert 'model_score' in result
    assert 'explanation' in result
    assert 'decision' in result
    assert 'reasons' in result
