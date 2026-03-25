KNOWLEDGE_DOCS = [
    {
        "title": "ACH Failure Patterns",
        "content": (
            "ACH payments can fail for reasons including invalid account details, insufficient funds, return "
            "codes, bank rejects, duplicate submissions, and cut-off timing issues. Operational teams often "
            "investigate return trends, same-day windows, and recurring beneficiaries with elevated failure rates."
        ),
    },
    {
        "title": "Wire Transfer Risk Signals",
        "content": (
            "Wire transfer risk is often linked to high-value amounts, sudden beneficiary changes, cross-border "
            "destinations, unusual customer behavior, and account takeover patterns. Fraud controls may pause wires "
            "for manual review when amount or geography deviates from normal customer activity."
        ),
    },
    {
        "title": "Card Fraud Risk Signals",
        "content": (
            "Card transaction risk signals include device mismatch, unusual merchant category usage, velocity spikes, "
            "international activity, and chargeback-linked patterns. Monitoring focuses on authorization failures, "
            "merchant anomalies, and suspicious geographic dispersion."
        ),
    },
    {
        "title": "Geo Mismatch Explained",
        "content": (
            "A geo mismatch occurs when transaction geography differs from a customer's expected location, prior "
            "patterns, or device context. This is commonly used as a fraud signal, especially when paired with a "
            "new device, beneficiary change, or unusually high amount."
        ),
    },
    {
        "title": "Velocity Risk Explained",
        "content": (
            "Velocity risk means the customer or device generated too many transactions within a short time window. "
            "This can indicate fraud automation, account takeover, mule activity, or repeated retries after failure."
        ),
    },
    {
        "title": "Payments Operations KPI Concepts",
        "content": (
            "Payments operations teams typically monitor failure rate, straight-through processing, manual review "
            "rate, fraud rate, average investigation time, false positive rate, and volume by rail. These metrics "
            "help identify service degradation and control effectiveness."
        ),
    },
]
