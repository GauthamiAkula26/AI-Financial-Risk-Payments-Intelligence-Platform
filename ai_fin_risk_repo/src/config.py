APP_TITLE = "AI Financial Risk & Payments Intelligence Platform"
APP_SUBTITLE = "Decision support for payments, fraud, and risk investigation"
from pathlib import Path
BASE_DIR = Path(__file__).resolve().parent.parent
DEFAULT_DATA_PATH = BASE_DIR / "data" / "sample" / "sample_transactions.csv"
HIGH_RISK_THRESHOLD = 75
