# RazorRisk AI

RazorRisk AI is a fintech-focused risk intelligence platform designed for a Razorpay-style hackathon. It combines a rules-based risk engine, model-style confidence scoring, event-driven transaction handling, and an optional LLM explanation layer for analyst-friendly narratives.

## Product idea

The product helps payment platforms detect suspicious transactions, merchant risk, unusual device activity, and repeat chargeback patterns before the payment is approved. It classifies each payment as:

- APPROVE
- REVIEW
- BLOCK

and explains the reason in plain language so operations teams can act quickly.

## Why this wins hackathons

- Strong, real-world fintech pain point
- Clear business value and measurable impact
- Explainable risk scoring instead of a black-box model
- Modern event-driven architecture and product UX
- Ready to extend into production with storage, monitoring, and deployment

## Production-ready upgrades included

- SQLite persistence for decision history
- environment-driven app configuration
- deployable Docker image and docker-compose setup
- event bus simulation for live risk ingestion
- hybrid scoring model with optional AI explanation layer

## Run locally

```bash
cd razorpay
python -m pip install -r requirements.txt
python app.py
```

Then open: http://localhost:5000

## Run with Docker

```bash
docker-compose up --build
```

## Environment configuration

Copy `.env.example` to `.env` and edit values as needed.

## Architecture summary

- payment event enters the system
- stream processor listens for new events
- risk engine evaluates policy and confidence signals
- engine returns decision + explanation
- dashboard shows live risk stream and operational metrics
- SQLite persists the decisions for audit and future operations

## Core problem solved

This system reduces payment fraud, chargeback exposure, and suspicious approval risk while preserving explainability for analysts and operators.
