from __future__ import annotations

from collections import defaultdict
from typing import Any


def build_network(transactions: list[dict[str, Any]]) -> dict[str, Any]:
    """Build a compact fraud-ring view from shared payment identities."""
    entities: dict[str, dict[str, Any]] = {}
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)

    for transaction in transactions:
        transaction_id = transaction.get('transaction_id', 'unknown')
        score = int(transaction.get('risk_score', 0))
        decision = transaction.get('decision', 'APPROVE')
        customer_id = transaction.get('customer_id') or transaction.get('customer_name')
        device_id = transaction.get('device_id')
        merchant_id = transaction.get('merchant_id') or transaction.get('merchant')

        if customer_id:
            entities[f'customer:{customer_id}'] = {
                'id': str(customer_id),
                'type': 'customer',
                'label': transaction.get('customer_name', customer_id),
            }
        if device_id:
            device_key = f'device:{device_id}'
            entities[device_key] = {'id': str(device_id), 'type': 'device', 'label': str(device_id)}
            groups[device_key].append(transaction)
        if merchant_id:
            merchant_key = f'merchant:{merchant_id}'
            entities[merchant_key] = {
                'id': str(merchant_id),
                'type': 'merchant',
                'label': transaction.get('merchant', merchant_id),
            }
            groups[merchant_key].append(transaction)

    connections = []
    for group_key, members in groups.items():
        if len(members) < 2:
            continue
        group_entity = entities[group_key]
        highest_risk = max(int(item.get('risk_score', 0)) for item in members)
        blocked_count = sum(item.get('decision') == 'BLOCK' for item in members)
        for transaction in members:
            customer_id = transaction.get('customer_id') or transaction.get('customer_name')
            if not customer_id:
                continue
            connections.append({
                'entity': group_entity['label'],
                'entity_type': group_entity['type'],
                'entity_id': group_entity['id'],
                'customer': transaction.get('customer_name', customer_id),
                'customer_id': str(customer_id),
                'transactions': len(members),
                'highest_risk': highest_risk,
                'blocked': blocked_count,
                'relationship': 'shared device' if group_entity['type'] == 'device' else 'shared merchant',
                'severity': 'critical' if highest_risk >= 75 else 'elevated' if highest_risk >= 45 else 'observed',
            })

    connections.sort(key=lambda item: (item['highest_risk'], item['transactions']), reverse=True)
    clusters = []
    seen = set()
    for connection in connections:
        key = (connection['entity_type'], connection['entity_id'])
        if key in seen:
            continue
        seen.add(key)
        clusters.append({
            'entity': connection['entity'],
            'entity_type': connection['entity_type'],
            'transactions': connection['transactions'],
            'highest_risk': connection['highest_risk'],
            'blocked': connection['blocked'],
            'severity': connection['severity'],
        })

    return {
        'connections': connections[:12],
        'clusters': clusters[:6],
        'summary': {
            'linked_transactions': sum(cluster['transactions'] for cluster in clusters),
            'suspicious_clusters': sum(cluster['highest_risk'] >= 45 for cluster in clusters),
            'critical_clusters': sum(cluster['highest_risk'] >= 75 for cluster in clusters),
        },
    }
