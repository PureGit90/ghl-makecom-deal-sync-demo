# Deal-Won Sync Pipeline with Error Handling — Working Automation Demo

## What This Does
Simulates the automation scenario that fires the moment a deal is marked "won" in GoHighLevel: it creates a matching invoice, spins up a project board card, and logs the deal to a reporting sheet — all in one pass, with retry logic and logging on every step so nothing fails silently.

## How It Works
GHL "deal won" webhook fires → Deal payload received (name, amount, client) → Parallel sync to invoicing, project board, and reporting sheet (each wrapped in retry + error handling) → Invoice, project card, and sheet row created; payment status can sync back to GHL → Step-by-step sync log confirms success or flags a failure for alerting

## Quick Start
1. `pip install -r requirements.txt`
2. `streamlit run app.py`
3. Fill in the deal form and click "Trigger Sync" to see the pipeline create an invoice, project card, and sheet row in real time. Check the "Simulate a step failure" box to see the retry logic kick in — one step will fail on its first attempt, then succeed on retry, with every step logged.

## Configuration
- This demo runs fully on mock data by design, showing the exact automation logic that would connect to live GoHighLevel + Make.com + invoicing/PM tool APIs

## Demo Limitations
- This is an MVP demo — it does not call real GoHighLevel, invoicing, project management, or Google Sheets APIs, and it doesn't yet send alerts to Slack/email when a step fails after retry
- Production version would add: live API authentication for each tool, a real Make.com webhook trigger, configurable retry counts/backoff, Slack or email failure alerts, and a lead-routing scenario feeding external leads into GHL
