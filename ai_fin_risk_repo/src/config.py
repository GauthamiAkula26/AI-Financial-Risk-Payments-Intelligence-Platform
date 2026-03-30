from pathlib import Path

APP_TITLE = "RiskLens AI"
APP_SUBTITLE = "Payment Intelligence & Fraud Operations Console"

BASE_DIR = Path(__file__).resolve().parent.parent
DEFAULT_DATA_PATH = BASE_DIR / "data" / "sample_transactions.csv"
HIGH_RISK_THRESHOLD = 75

ROLE_OPTIONS = [
    "Fraud Analyst",
    "Payments Ops Manager",
    "Product Manager",
    "Compliance Reviewer",
]

PAGE_OPTIONS = [
    "Command Center",
    "Investigations",
    "Payment Intelligence",
    "Alerts & Cases",
    "Rules & Explainability",
    "Admin / Data",
]

REQUIRED_COLUMNS = [
    "transaction_id",
    "customer_id",
    "amount",
    "currency",
    "payment_rail",
    "channel",
    "risk_score",
    "status",
    "is_fraud_label",
    "device_id",
    "ip_address",
    "geo_mismatch_flag",
    "origin_country",
    "destination_country",
    "merchant_category",
    "timestamp",
    "velocity_flag",
    "beneficiary_change_flag",
    "customer_txn_count_24h",
    "historical_customer_avg_amount",
    "failure_code",
    "direction",
]
