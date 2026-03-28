from pathlib import Path

APP_TITLE = "RiskLens AI"
APP_SUBTITLE = "AI Financial Risk & Payments Intelligence Platform for payments, fraud, and risk investigation"

BASE_DIR = Path(__file__).resolve().parent.parent
DEFAULT_DATA_PATH = BASE_DIR / "data" / "sample_transactions.csv"
HIGH_RISK_THRESHOLD = 75
