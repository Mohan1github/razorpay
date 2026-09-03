from __future__ import annotations

import random
import threading
import time
from collections import deque
from datetime import datetime, timezone
from typing import Any

from src.risk_engine import score_transaction


EVENT_QUEUE: deque[dict[str, Any]] = deque()
_EVENT_LOCK = threading.Lock()


class EventBusListener:
    """Simulates a live event-bus consumer for payment events from a Razorpay-like stream."""

    def __init__(self, topic: str = 'razorpay.payment.events', on_event=None):
        self.topic = topic
        self.on_event = on_event
        self.running = False
        self.thread = None
        self.producer_thread = None
        self._event_index = 8

    def start(self):
        if self.running:
            return
        self.running = True
        self.thread = threading.Thread(target=self._consume_loop, daemon=True)
        self.thread.start()
        self.producer_thread = threading.Thread(target=self._produce_loop, daemon=True)
        self.producer_thread.start()

    def stop(self):
        self.running = False

    def _consume_loop(self):
        while self.running:
            with _EVENT_LOCK:
                event = EVENT_QUEUE.popleft() if EVENT_QUEUE else None
            if event:
                self._process_event(event)
            time.sleep(0.2)

    def _produce_loop(self):
        profiles = ['safe', 'review', 'safe', 'block', 'review']
        while self.running:
            event = _gateway_like_event(self._event_index, profiles[self._event_index % len(profiles)])
            with _EVENT_LOCK:
                EVENT_QUEUE.append(event)
            self._event_index += 1
            time.sleep(3)

    def _process_event(self, event: dict[str, Any]):
        score = score_transaction(event)
        event.update(score)
        event['source'] = 'event-bus-listener'
        event['event_type'] = 'payment_event'
        if self.on_event:
            self.on_event(event)


def _gateway_like_event(index: int, risk_profile: str) -> dict[str, Any]:
    merchants = {
        'CloudCart': {'merchant_id': 'm_1001', 'merchant_risk_score': 0.32, 'country': 'IN'},
        'TravelPrime': {'merchant_id': 'm_1002', 'merchant_risk_score': 0.81, 'country': 'IN'},
        'GroceryHub': {'merchant_id': 'm_1003', 'merchant_risk_score': 0.44, 'country': 'US'},
        'ZestPay': {'merchant_id': 'm_1004', 'merchant_risk_score': 0.67, 'country': 'IN'},
        'ApexBooks': {'merchant_id': 'm_1005', 'merchant_risk_score': 0.28, 'country': 'AE'},
        'UrbanMobility': {'merchant_id': 'm_1006', 'merchant_risk_score': 0.59, 'country': 'IN'},
        'NovaGaming': {'merchant_id': 'm_1007', 'merchant_risk_score': 0.76, 'country': 'US'},
        'AlphaRetail': {'merchant_id': 'm_1008', 'merchant_risk_score': 0.39, 'country': 'SG'},
    }

    customers = [
        ('Aarav Mehta', 'cust_1001', 'dev_5001'),
        ('Priya Nair', 'cust_1002', 'dev_5002'),
        ('Karan Shah', 'cust_1003', 'dev_5003'),
        ('Neha Verma', 'cust_1004', 'dev_5004'),
        ('Rohit Puri', 'cust_1005', 'dev_5005'),
        ('Ishita Rao', 'cust_1006', 'dev_5006'),
        ('Vikram Singh', 'cust_1007', 'dev_5007'),
        ('Sana Ali', 'cust_1008', 'dev_5008'),
    ]

    merchant_name, merchant_meta = list(merchants.items())[index % len(merchants)]
    customer_name, customer_id, _ = customers[index % len(customers)]
    device_id = f'dev_{5001 + (index % 4)}'

    risk_profiles = {
        'safe': {
            'amount': random.randint(300, 3500),
            'merchant_risk_score': random.uniform(0.1, 0.35),
            'device_risk': random.uniform(0.08, 0.22),
            'velocity': random.randint(1, 2),
            'transaction_hour': random.randint(9, 18),
            'failure_count': random.randint(0, 1),
            'is_new_customer': False,
            'historical_chargebacks': random.randint(0, 1),
            'country_mismatch': False,
        },
        'review': {
            'amount': random.randint(5000, 18000),
            'merchant_risk_score': random.uniform(0.45, 0.75),
            'device_risk': random.uniform(0.38, 0.7),
            'velocity': random.randint(3, 6),
            'transaction_hour': random.choice([0, 1, 2, 3, 23]),
            'failure_count': random.randint(1, 3),
            'is_new_customer': random.choice([True, False]),
            'historical_chargebacks': random.randint(1, 3),
            'country_mismatch': random.choice([True, False]),
        },
        'block': {
            'amount': random.randint(20000, 50000),
            'merchant_risk_score': random.uniform(0.7, 0.95),
            'device_risk': random.uniform(0.7, 0.95),
            'velocity': random.randint(6, 12),
            'transaction_hour': random.choice([0, 1, 2, 3, 4]),
            'failure_count': random.randint(2, 5),
            'is_new_customer': True,
            'historical_chargebacks': random.randint(2, 5),
            'country_mismatch': True,
        },
    }

    profile = risk_profiles[risk_profile]
    event = {
        'transaction_id': f'TXN-{1000 + index}',
        'payment_id': f'pay_{100000 + index}',
        'order_id': f'ord_{200000 + index}',
        'merchant_id': merchant_meta['merchant_id'],
        'merchant': merchant_name,
        'customer_id': customer_id,
        'customer_name': customer_name,
        'device_id': device_id,
        'amount': profile['amount'],
        'currency': 'INR',
        'payment_method': random.choice(['UPI', 'CARD', 'NETBANKING', 'WALLET']),
        'country': 'IN',
        'ip_country': random.choice(['IN', 'US', 'SG', 'AE']),
        'source': 'payment-gateway',
        'event_type': 'payment_event',
        'merchant_risk_score': round(profile['merchant_risk_score'], 2),
        'device_risk': round(profile['device_risk'], 2),
        'velocity': profile['velocity'],
        'transaction_hour': profile['transaction_hour'],
        'failure_count': profile['failure_count'],
        'is_new_customer': profile['is_new_customer'],
        'historical_chargebacks': profile['historical_chargebacks'],
        'country_mismatch': profile['country_mismatch'],
        'timestamp': datetime.now(timezone.utc).isoformat(),
    }

    event['device_risk_score'] = event['device_risk']
    event['merchant_reference_country'] = merchant_meta['country']
    event['risk_context'] = {
        'hour_of_day': event['transaction_hour'],
        'retry_count': event['failure_count'],
        'bin_country': event['country'],
        'email_domain': 'gmail.com',
    }
    return event


def build_event_stream() -> list[dict[str, Any]]:
    profiles = ['safe', 'review', 'block', 'safe', 'review', 'block', 'safe', 'review']
    payload = []
    for i, profile in enumerate(profiles):
        tx = _gateway_like_event(i, profile)
        tx.update(score_transaction(tx))
        payload.append(tx)
    return payload


def emit_event(event: dict[str, Any]) -> dict[str, Any]:
    enriched = {**event, **score_transaction(event)}
    with _EVENT_LOCK:
        EVENT_QUEUE.append(enriched)
    return enriched
