from __future__ import annotations

import json
from collections import Counter, defaultdict

from flask import Flask, jsonify, render_template, request

from src.config import APP_CONFIG
from src.database import count_transactions, fetch_recent_transactions, init_db, save_transaction
from src.risk_engine import score_transaction, summarize_decision_summary
from src.network_investigator import build_network
from src.risk_agent import run_riskops_agent
from src.stream_processor import EventBusListener, build_event_stream, emit_event

app = Flask(__name__)
app.config.update(APP_CONFIG)

init_db()
RISK_EVENTS = build_event_stream()


def handle_stream_event(event):
    RISK_EVENTS.insert(0, event)
    del RISK_EVENTS[20:]
    save_transaction(event)


EVENT_LISTENER = EventBusListener(on_event=handle_stream_event)
EVENT_LISTENER.start()


def build_dashboard_context():
    persisted = fetch_recent_transactions(limit=20)
    txs = list(RISK_EVENTS) if RISK_EVENTS else []
    if not txs:
        txs = []
        for row in persisted:
            event = dict(row)
            event['reasons'] = event.get('reasons') or []
            txs.append(event)

    summary = summarize_decision_summary(txs)
    risk_rate = round(((summary['blocked'] + summary['review']) / max(len(txs), 1)) * 100, 1)

    signal_counts = Counter()
    merchant_stats = defaultdict(lambda: {'risk_total': 0, 'events': 0})
    decision_counts = Counter()

    for tx in txs:
        decision_counts[tx.get('decision', 'APPROVE')] += 1
        for reason in tx.get('reasons', []):
            signal_counts[reason] += 1
        merchant = tx.get('merchant', 'Unknown')
        merchant_stats[merchant]['risk_total'] += tx.get('risk_score', 0)
        merchant_stats[merchant]['events'] += 1

    top_signals = [
        {'label': label, 'count': count}
        for label, count in signal_counts.most_common(4)
    ]

    merchant_watchlist = [
        {
            'merchant': merchant,
            'risk': round(stats['risk_total'] / max(stats['events'], 1)),
            'events': stats['events'],
        }
        for merchant, stats in sorted(
            merchant_stats.items(),
            key=lambda item: item[1]['risk_total'] / max(item[1]['events'], 1),
            reverse=True,
        )[:3]
    ]

    decision_mix = [
        {'label': decision, 'value': count}
        for decision, count in [
            ('APPROVE', decision_counts.get('APPROVE', 0)),
            ('REVIEW', decision_counts.get('REVIEW', 0)),
            ('BLOCK', decision_counts.get('BLOCK', 0)),
        ]
    ]

    risk_trend = [
        {'label': f'T{x + 1}', 'value': tx.get('risk_score', 0)}
        for x, tx in enumerate(txs[:8])
    ]

    summary.update({
        'total_volume': len(txs),
        'risk_rate': risk_rate,
        'top_signals': top_signals,
        'merchant_watchlist': merchant_watchlist,
        'decision_mix': decision_mix,
        'risk_trend': risk_trend,
    })

    return txs, summary


@app.route('/')
def index():
    txs, summary = build_dashboard_context()
    return render_template('index.html', transactions=txs, summary=summary)


@app.route('/api/transactions')
def api_transactions():
    txs, summary = build_dashboard_context()
    return jsonify({'transactions': txs, 'summary': summary})


@app.route('/api/analytics')
def api_analytics():
    _, summary = build_dashboard_context()
    return jsonify({
        'truth': 'live-risk-analytics',
        'decision_mix': summary.get('decision_mix', []),
        'risk_trend': summary.get('risk_trend', []),
        'merchant_watchlist': summary.get('merchant_watchlist', []),
    })


@app.route('/api/network')
def api_network():
    txs, _ = build_dashboard_context()
    return jsonify(build_network(txs))


@app.route('/api/agent/investigate')
def api_agent_investigate():
    txs, _ = build_dashboard_context()
    return jsonify(run_riskops_agent(txs))


@app.route('/api/risk/score', methods=['POST'])
def api_risk_score():
    payload = request.get_json(silent=True) or {}
    if not payload:
        return jsonify({'error': 'No JSON payload supplied.'}), 400

    tx = {
        'transaction_id': payload.get('transaction_id') or f"TXN-{len(RISK_EVENTS) + 1000}",
        'customer_name': payload.get('customer_name') or 'Unknown Customer',
        'merchant': payload.get('merchant') or 'Unknown Merchant',
        'amount': float(payload.get('amount', 0)),
        'merchant_risk_score': float(payload.get('merchant_risk_score', 0)),
        'device_risk': float(payload.get('device_risk', 0)),
        'velocity': int(payload.get('velocity', 0)),
        'transaction_hour': int(payload.get('transaction_hour', 12)),
        'failure_count': int(payload.get('failure_count', 0)),
        'is_new_customer': bool(payload.get('is_new_customer', False)),
        'historical_chargebacks': int(payload.get('historical_chargebacks', 0)),
        'country_mismatch': bool(payload.get('country_mismatch', False)),
        'source': payload.get('source', 'manual-input'),
        'event_type': payload.get('event_type', 'payment_event'),
    }

    enriched = emit_event(tx)
    handle_stream_event(enriched)
    return jsonify(enriched)


@app.route('/api/health')
def api_health():
    return jsonify({
        'status': 'ok',
        'service': 'razorrisk-ai',
        'stream': 'real-time-payment-risk-monitor',
        'environment': 'production-simulated',
        'database_records': count_transactions(),
    })


if __name__ == '__main__':
    app.run(debug=APP_CONFIG['DEBUG'], host=APP_CONFIG['HOST'], port=APP_CONFIG['PORT'])
