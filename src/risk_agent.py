from __future__ import annotations

from typing import Any

from src.network_investigator import build_network


def run_riskops_agent(transactions: list[dict[str, Any]]) -> dict[str, Any]:
    """Produce a recommendation-only investigation from existing risk signals."""
    network = build_network(transactions)
    clusters = network['clusters']
    critical = [cluster for cluster in clusters if cluster['severity'] == 'critical']
    latest = transactions[0] if transactions else {}
    latest_score = int(latest.get('risk_score', 0))

    if critical:
        cluster = critical[0]
        recommendation = 'BLOCK_DEVICE' if cluster['entity_type'] == 'device' else 'REVIEW_MERCHANT'
        finding = (
            f"{cluster['transactions']} payments are connected through {cluster['entity_type']} "
            f"{cluster['entity']} with a peak risk of {cluster['highest_risk']}."
        )
        priority = 'CRITICAL'
        confidence = min(99, 82 + cluster['transactions'] * 4)
        actions = [
            f"Temporarily restrict {cluster['entity']}",
            'Review every linked payment and customer',
            'Escalate the merchant to fraud operations',
        ]
    elif latest_score >= 45:
        recommendation = 'REVIEW_PAYMENT'
        finding = f"Latest payment {latest.get('transaction_id', 'event')} combines multiple elevated risk signals."
        priority = 'ELEVATED'
        confidence = 78
        actions = ['Route payment to manual review', 'Request additional customer verification']
    else:
        recommendation = 'MONITOR'
        finding = 'No critical coordinated activity detected in the current payment window.'
        priority = 'LOW'
        confidence = 71
        actions = ['Continue monitoring the live stream']

    return {
        'agent': 'RiskOps Investigation Agent',
        'status': 'MONITORING',
        'priority': priority,
        'finding': finding,
        'recommendation': recommendation,
        'confidence': confidence,
        'actions': actions,
        'linked_entities': len(clusters),
        'human_approval_required': True,
    }
