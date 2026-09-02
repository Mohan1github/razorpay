from __future__ import annotations

import random
import threading
import time
from collections import deque
from typing import Any

from src.risk_engine import score_transaction


EVENT_QUEUE: deque[dict[str, Any]] = deque()
_EVENT_LOCK = threading.Lock()


class EventBusListener:
    """Simulates a live event-bus consumer for payment events from a Razorpay-like stream."""

    def __init__(self, topic: str = 'razorpay.payment.events'):
        self.topic = topic
        self.running = False
        self.thread = None

    def start(self):
        if self.running:
            return
        self.running = True
        self.thread = threading.Thread(target=self._consume_loop, daemon=True)
        self.thread.start()

    def stop(self):
        self.running = False

    def _consume_loop(self):
        while self.running:
            if EVENT_QUEUE:
                event = EVENT_QUEUE.popleft()
                self._process_event(event)
            time.sleep(0.2)

    def _process_event(self, event: dict[str, Any]):
        score = score_transaction(event)
        event.update(score)
        event['source'] = 'event-bus-listener'
        event['event_type'] = 'payment_event'


def build_event_stream() -> list[dict[str, Any]]:
    merchants = [
        'CloudCart',
        'TravelPrime',
        'GroceryHub',
        'ZestPay',
        'ApexBooks',
        'UrbanMobility',
        'NovaGaming',
        'AlphaRetail',
    ]

    customers = [
        'Aarav Mehta',
        'Priya Nair',
        'Karan Shah',
        'Neha Verma',
        'Rohit Puri',
        'Ishita Rao',
        'Vikram Singh',
        'Sana Ali',
    ]

    payload = []
    for i in range(8):
        transaction = {
            'transaction_id': f'TXN-{1000 + i}',
            'customer_name': customers[i % len(customers)],
            'merchant': merchants[i % len(merchants)],
            'amount': random.randint(300, 22000),
            'merchant_risk_score': round(random.uniform(0.1, 0.95), 2),
            'device_risk': round(random.uniform(0.05, 0.9), 2),
            'velocity': random.randint(1, 9),
            'transaction_hour': random.randint(0, 23),
            'failure_count': random.randint(0, 4),
            'is_new_customer': random.choice([True, False]),
            'historical_chargebacks': random.randint(0, 5),
            'country_mismatch': random.choice([True, False]),
            'source': 'payment-gateway',
            'event_type': 'payment_event',
        }
        enriched = {**transaction, **score_transaction(transaction)}
        payload.append(enriched)

    return payload


def emit_event(event: dict[str, Any]) -> dict[str, Any]:
    enriched = {**event, **score_transaction(event)}
    with _EVENT_LOCK:
        EVENT_QUEUE.append(enriched)
    return enriched
