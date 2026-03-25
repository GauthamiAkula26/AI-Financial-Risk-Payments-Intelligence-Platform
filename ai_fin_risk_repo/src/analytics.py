from __future__ import annotations

from typing import Dict, Optional

import pandas as pd

from src.rules_engine import evaluate_transaction_risk


class AnalyticsEngine:
    def __init__(self, df: pd.DataFrame):
        self.df = df.copy()
        self.df[["risk_score", "risk_band", "risk_reasons"]] = self.df.apply(
            lambda row: pd.Series(self._score_row(row)), axis=1
        )

    @staticmethod
    def _score_row(row: pd.Series):
        out = evaluate_transaction_risk(row.to_dict())
        return out["risk_score"], out["risk_band"], "; ".join(out["reasons"])

    def summary_metrics(self) -> Dict:
        total = len(self.df)
        failed = int((self.df["status"] == "FAILED").sum())
        fraud = int(self.df["is_fraud_label"].sum())
        high_risk = int((self.df["risk_band"] == "HIGH").sum())
        failure_rate = round((failed / total) * 100, 2) if total else 0
        fraud_rate = round((fraud / total) * 100, 2) if total else 0
        return {
            "total_transactions": total,
            "failed_transactions": failed,
            "failure_rate": failure_rate,
            "fraud_flagged": fraud,
            "fraud_rate": fraud_rate,
            "high_risk_transactions": high_risk,
        }

    def get_transaction(self, transaction_id: str) -> Optional[Dict]:
        match = self.df[self.df["transaction_id"].astype(str).str.upper() == transaction_id.upper()]
        if match.empty:
            return None
        return match.iloc[0].to_dict()

    def failures_by_rail(self) -> pd.DataFrame:
        grouped = (
            self.df.assign(is_failed=self.df["status"].eq("FAILED").astype(int))
            .groupby("payment_rail", as_index=False)
            .agg(total_transactions=("transaction_id", "count"), failed_transactions=("is_failed", "sum"))
        )
        grouped["failure_rate_pct"] = (grouped["failed_transactions"] / grouped["total_transactions"] * 100).round(2)
        return grouped.sort_values("failure_rate_pct", ascending=False)

    def risk_patterns(self) -> pd.DataFrame:
        patterns = pd.DataFrame(
            {
                "pattern": [
                    "Geo mismatch",
                    "Velocity flagged",
                    "Beneficiary changed",
                    "High amount (>10k)",
                    "Failed + high risk",
                ],
                "count": [
                    int(self.df["geo_mismatch_flag"].sum()),
                    int(self.df["velocity_flag"].sum()),
                    int(self.df["beneficiary_change_flag"].sum()),
                    int((self.df["amount"] > 10000).sum()),
                    int(((self.df["status"] == "FAILED") & (self.df["risk_band"] == "HIGH")).sum()),
                ],
            }
        )
        return patterns.sort_values("count", ascending=False)

    def filter_transactions(
        self,
        rail: str = "ALL",
        status: str = "ALL",
        risk_band: str = "ALL",
    ) -> pd.DataFrame:
        df = self.df.copy()
        if rail != "ALL":
            df = df[df["payment_rail"] == rail]
        if status != "ALL":
            df = df[df["status"] == status]
        if risk_band != "ALL":
            df = df[df["risk_band"] == risk_band]
        return df.sort_values("timestamp", ascending=False)
