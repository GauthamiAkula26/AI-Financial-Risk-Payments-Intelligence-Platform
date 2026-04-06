# RiskLens AI

**Payment Intelligence & Fraud Operations Console**

RiskLens AI is an analyst-facing decision-support platform for payments, fraud, and risk operations. It combines payment rail intelligence, explainable risk scoring, investigation workflows, and manual review prioritization into a single workspace.

---

## Why this project

Payments and fraud teams often work across fragmented tools, static dashboards, spreadsheets, and manual investigation workflows.

RiskLens AI is designed to bring those workflows together in one UI that supports:

- fraud analysts investigating suspicious activity
- payments operations managers monitoring rail health
- product managers balancing fraud controls and customer friction
- compliance reviewers needing explainable, audit-friendly rationale

---

## Core capabilities

### 1. Role-based dashboards
The app supports multiple user views:

- **Fraud Analyst**
- **Payments Ops Manager**
- **Product Manager**
- **Compliance Reviewer**

Each role sees the same data through a different decision-making lens.

### 2. Command Center
A top-level operational dashboard with:

- total volume
- approval rate
- review queue
- failure rate
- fraud rate
- top risk rail
- corridor risk insights

### 3. Investigations workspace
An analyst-focused page that supports:

- natural language investigation prompts
- transaction-level review
- knowledge context
- case note generation
- downloadable investigation report

### 4. Payment rail intelligence
A dedicated page for payments monitoring across:

- ACH
- Wire
- RTP
- Card

It surfaces:

- average risk by rail
- fraud rate by rail
- failure / review rate by rail
- average amount by rail
- risk by channel and rail
- failure code intelligence

### 5. Alerts & Cases
A workflow-oriented queue for transactions that need review, including:

- case ID
- severity
- assigned owner
- case status
- signals triggered
- recommended action

### 6. Rules & Explainability
An explainability layer that shows:

- score breakdown
- triggered signals
- contribution by signal
- recommended action

---

## Product screens

- **Command Center**
- **Investigations**
- **Payment Intelligence**
- **Alerts & Cases**
- **Rules & Explainability**
- **Admin / Data**

---

## Architecture

See [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md)

---

## Dataset schema

The sample dataset includes enterprise-style transaction features such as:

- `transaction_id`
- `customer_id`
- `amount`
- `currency`
- `payment_rail`
- `channel`
- `risk_score`
- `status`
- `is_fraud_label`
- `device_id`
- `geo_mismatch_flag`
- `origin_country`
- `destination_country`
- `velocity_flag`
- `beneficiary_change_flag`
- `customer_txn_count_24h`
- `historical_customer_avg_amount`
- `failure_code`

---

## Tech stack

- Python
- Streamlit
- Pandas
- Plotly
- Lightweight retrieval-based knowledge context
- CSV-based synthetic payments dataset

---

## Getting started

### Run locally

```bash
cd ai_fin_risk_repo
pip install -r requirements.txt
streamlit run app.py
