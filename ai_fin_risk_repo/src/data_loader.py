from __future__ import annotations

import pandas as pd


REQUIRED_COLUMNS = {
    "transaction_id",
    "timestamp",
    "customer_id",
    "payment_rail",
    "direction",
    "amount",
    "currency",
    "origin_country",
    "destination_country",
    "merchant_category",
    "channel",
    "device_id",
    "ip_address",
    "status",
    "failure_code",
    "is_fraud_label",
    "historical_customer_avg_amount",
    "customer_txn_count_24h",
    "beneficiary_change_flag",
    "geo_mismatch_flag",
    "velocity_flag",
}


def load_transactions(file_or_path) -> pd.DataFrame:
    df = pd.read_csv(file_or_path)
    missing = REQUIRED_COLUMNS - set(df.columns)
    if missing:
        raise ValueError(f"Dataset is missing required columns: {sorted(missing)}")

    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
    df["amount"] = pd.to_numeric(df["amount"], errors="coerce")
    df["historical_customer_avg_amount"] = pd.to_numeric(
        df["historical_customer_avg_amount"], errors="coerce"
    )
    df["customer_txn_count_24h"] = pd.to_numeric(df["customer_txn_count_24h"], errors="coerce")

    for col in [
        "is_fraud_label",
        "beneficiary_change_flag",
        "geo_mismatch_flag",
        "velocity_flag",
    ]:
        df[col] = df[col].astype(str).str.lower().isin(["1", "true", "yes"])

    df["status"] = df["status"].astype(str).str.upper()
    df["payment_rail"] = df["payment_rail"].astype(str).str.upper()
    df["direction"] = df["direction"].astype(str).str.upper()

    return df
