from __future__ import annotations

from typing import Dict, List


def evaluate_transaction_risk(txn: Dict) -> Dict:
    score = 0
    reasons: List[str] = []

    amount = float(txn.get("amount", 0) or 0)
    avg_amount = float(txn.get("historical_customer_avg_amount", 0) or 0)
    payment_rail = str(txn.get("payment_rail", "")).upper()
    status = str(txn.get("status", "")).upper()
    customer_txn_count_24h = float(txn.get("customer_txn_count_24h", 0) or 0)

    if amount >= 10000:
        score += 25
        reasons.append("High transaction amount")

    if avg_amount > 0 and amount >= (avg_amount * 3):
        score += 20
        reasons.append("Amount is materially above historical customer average")

    if bool(txn.get("beneficiary_change_flag", False)):
        score += 20
        reasons.append("Recent beneficiary change detected")

    if bool(txn.get("geo_mismatch_flag", False)):
        score += 15
        reasons.append("Geographic mismatch detected")

    if bool(txn.get("velocity_flag", False)) or customer_txn_count_24h >= 5:
        score += 15
        reasons.append("Velocity risk / unusually high recent transaction count")

    if payment_rail == "WIRE" and amount >= 5000:
        score += 10
        reasons.append("Wire transactions require stronger scrutiny at higher values")

    if status == "FAILED":
        score += 10
        reasons.append("Transaction failed and may indicate retry or data-quality risk")

    if bool(txn.get("is_fraud_label", False)):
        score += 25
        reasons.append("Fraud label present in source data")

    risk_band = "LOW"
    if score >= 75:
        risk_band = "HIGH"
    elif score >= 40:
        risk_band = "MEDIUM"

    return {"risk_score": min(score, 100), "risk_band": risk_band, "reasons": reasons}
