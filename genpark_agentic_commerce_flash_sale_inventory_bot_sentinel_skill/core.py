# -*- coding: utf-8 -*-
"""Flash Sale Inventory Bot Sentinel Skill for GenPark Agentic Commerce."""
import json
import hashlib
import time
from typing import Dict, Any

def evaluate_checkout_intent_risk(interaction_duration_ms: int, requests_per_minute: int, account_age_days: int, user_agent: str = "Mozilla/5.0", keystroke_entropy: float = 0.8) -> Dict[str, Any]:
    risk_points = 0
    signals = []

    # Velocity and duration checks
    if interaction_duration_ms < 600:
        risk_points += 45
        signals.append("Sub-human checkout velocity (<600ms latency indicates headless scripted submission)")
    elif interaction_duration_ms < 1500:
        risk_points += 20
        signals.append("Unusually rapid checkout execution")

    if requests_per_minute > 30:
        risk_points += 35
        signals.append(f"Excessive request burst rate ({requests_per_minute} rpm)")

    if keystroke_entropy < 0.3:
        risk_points += 25
        signals.append("Synthetic robotic typing cadence (low Shannon entropy)")

    if account_age_days < 1:
        risk_points += 20
        signals.append("Freshly minted throwaway account (<24 hours old)")
    elif account_age_days < 7:
        risk_points += 10

    # User-agent heuristics
    ua_lower = user_agent.lower()
    if any(bot_id in ua_lower for bot_id in ["headless", "puppeteer", "playwright", "selenium", "python-requests"]):
        risk_points += 50
        signals.append(f"Automated bot user-agent detected: {user_agent[:30]}")

    final_risk_score = min(100.0, float(risk_points))
    
    if final_risk_score >= 60.0:
        decision = "BLOCK_AND_CHALLENGE"
    elif final_risk_score >= 35.0:
        decision = "QUEUE_FOR_RATE_LIMIT"
    else:
        decision = "ALLOW_IMMEDIATE_SETTLEMENT"

    return {
        "risk_score": final_risk_score,
        "decision": decision,
        "is_bot_suspected": final_risk_score >= 50.0,
        "detected_anomalies": signals,
        "evaluated_at_epoch": int(time.time()),
        "firewall_profile": "GenPark Commerce Edge Sentinel"
    }

def allocate_inventory_reservation_slice(sku_id: str, requested_quantity: int, risk_score: float, available_stock: int) -> Dict[str, Any]:
    if available_stock <= 0:
        return {"status": "OUT_OF_STOCK", "allocated_quantity": 0, "reason": "No inventory remaining"}

    if risk_score >= 60.0:
        return {
            "status": "CHALLENGE_REQUIRED",
            "allocated_quantity": 0,
            "action_required": "Pass proof-of-work cryptographic challenge or biometric verification.",
            "ttl_seconds": 60
        }

    # Strict allocation limit for flash sales: max 2 units per transaction
    approved_qty = min(min(2, requested_quantity), available_stock)
    hold_token = hashlib.sha256(f"{sku_id}_{approved_qty}_{time.time()}".encode()).hexdigest()[:16].upper()

    return {
        "status": "RESERVED",
        "sku_id": sku_id,
        "allocated_quantity": approved_qty,
        "remaining_unallocated_stock": available_stock - approved_qty,
        "reservation_hold_token": f"HOLD-{hold_token}",
        "reservation_ttl_seconds": 180,
        "checkout_url": f"https://checkout.genpark.ai/cart/reserve?token=HOLD-{hold_token}"
    }
