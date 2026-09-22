"""
Deal-Won Sync Pipeline with Error Handling
--------------------------------------------
Core automation logic representing a Make.com scenario triggered by a
GoHighLevel (GHL) "deal won" webhook. When a deal is marked won, this
pipeline fans out to create matching records in an invoicing tool, a
project management board, and a Google Sheets reporting log -- with
retry logic, structured logging, and failure alerting on every step.

Every function here runs on mock data by design. In production, each
_mock_* function would be replaced with an authenticated API call to
the real invoicing tool, PM board, and Google Sheets, using the same
call signature and the same error handling / retry wrapper.
"""

import random
import uuid
from datetime import datetime, timedelta


def _mock_create_invoice(deal: dict) -> dict:
    """Simulate creating a draft invoice in the invoicing platform from a won deal."""
    invoice_id = f"INV-{uuid.uuid4().hex[:8].upper()}"
    due_date = (datetime.now() + timedelta(days=14)).strftime("%Y-%m-%d")
    return {
        "invoice_id": invoice_id,
        "amount": deal.get("amount"),
        "client_name": deal.get("client_name"),
        "deal_name": deal.get("deal_name"),
        "due_date": due_date,
        "status": "draft",
    }


def _mock_create_project(deal: dict) -> dict:
    """Simulate creating a new project management board card for a won deal."""
    project_id = f"PROJ-{uuid.uuid4().hex[:8].upper()}"
    return {
        "project_id": project_id,
        "board_column": "Kickoff",
        "assigned_owner": "Unassigned (pending PM triage)",
        "linked_deal_id": deal.get("deal_id", deal.get("deal_name")),
    }


def _mock_append_sheet_row(deal: dict) -> dict:
    """Simulate appending a reporting row to the Google Sheets revenue log."""
    row_number = random.randint(100, 999)
    columns_written = ["Deal Name", "Client", "Amount", "Date Won", "Invoice ID", "Project ID"]
    return {
        "row_number": row_number,
        "columns_written": columns_written,
        "sheet_name": "Deal Revenue Log",
    }


def sync_deal_won(deal: dict, simulate_failure: bool = False) -> dict:
    """
    Orchestration function representing the Make.com scenario triggered by
    a GHL 'deal won' webhook. Runs invoicing, project creation, and sheet
    logging in sequence, with per-step error handling and a single retry
    on failure. Returns a result dict with per-step status and a
    human-readable sync log, so failures are visible instead of silent.
    """
    steps = []
    sync_log = []
    records = {}

    # Decide which step (if any) fails on its first attempt.
    failing_step = "invoice" if simulate_failure else None

    # --- Step 1/3: Invoice creation ---
    sync_log.append("Step 1/3: Creating invoice...")
    try:
        if failing_step == "invoice":
            raise ConnectionError("timeout")
        invoice = _mock_create_invoice(deal)
        records["invoice"] = invoice
        steps.append({"step": "Invoice creation", "status": "success"})
        sync_log.append(f"Step 1/3: Invoice creation succeeded ({invoice['invoice_id']})")
    except Exception as exc:
        sync_log.append(f"Step 1/3: Invoice creation failed ({exc}) - retrying...")
        try:
            invoice = _mock_create_invoice(deal)
            records["invoice"] = invoice
            steps.append({"step": "Invoice creation", "status": "retried-then-success"})
            sync_log.append(f"Step 1/3: Invoice creation succeeded on retry ({invoice['invoice_id']})")
        except Exception as exc2:
            steps.append({"step": "Invoice creation", "status": "failed"})
            sync_log.append(f"Step 1/3: Invoice creation failed again ({exc2}) - ALERT: manual review required")
            records["invoice"] = None

    # --- Step 2/3: Project card creation ---
    sync_log.append("Step 2/3: Creating project board card...")
    try:
        project = _mock_create_project(deal)
        records["project"] = project
        steps.append({"step": "Project card creation", "status": "success"})
        sync_log.append(f"Step 2/3: Project card creation succeeded ({project['project_id']})")
    except Exception as exc:
        sync_log.append(f"Step 2/3: Project card creation failed ({exc}) - retrying...")
        try:
            project = _mock_create_project(deal)
            records["project"] = project
            steps.append({"step": "Project card creation", "status": "retried-then-success"})
            sync_log.append(f"Step 2/3: Project card creation succeeded on retry ({project['project_id']})")
        except Exception as exc2:
            steps.append({"step": "Project card creation", "status": "failed"})
            sync_log.append(f"Step 2/3: Project card creation failed again ({exc2}) - ALERT: manual review required")
            records["project"] = None

    # --- Step 3/3: Reporting sheet row ---
    sync_log.append("Step 3/3: Logging to reporting sheet...")
    try:
        sheet_row = _mock_append_sheet_row(deal)
        records["sheet_row"] = sheet_row
        steps.append({"step": "Reporting sheet log", "status": "success"})
        sync_log.append(f"Step 3/3: Reporting sheet log succeeded (row {sheet_row['row_number']})")
    except Exception as exc:
        sync_log.append(f"Step 3/3: Reporting sheet log failed ({exc}) - retrying...")
        try:
            sheet_row = _mock_append_sheet_row(deal)
            records["sheet_row"] = sheet_row
            steps.append({"step": "Reporting sheet log", "status": "retried-then-success"})
            sync_log.append(f"Step 3/3: Reporting sheet log succeeded on retry (row {sheet_row['row_number']})")
        except Exception as exc2:
            steps.append({"step": "Reporting sheet log", "status": "failed"})
            sync_log.append(f"Step 3/3: Reporting sheet log failed again ({exc2}) - ALERT: manual review required")
            records["sheet_row"] = None

    all_success = all(s["status"] in ("success", "retried-then-success") for s in steps)
    sync_log.append("Sync complete: all steps succeeded" if all_success else "Sync complete: one or more steps failed after retry - alert sent")

    return {
        "deal_name": deal.get("deal_name"),
        "steps": steps,
        "sync_log": sync_log,
        "records": records,
        "overall_status": "success" if all_success else "failed_with_alert",
    }


def sync_payment_status_back(invoice_id: str, status: str) -> dict:
    """
    Simulate the reverse sync: when an invoice is marked paid in the
    invoicing platform, push that status back into the GHL deal record
    (e.g. as a custom field or pipeline stage update).
    """
    return {
        "invoice_id": invoice_id,
        "ghl_field_updated": "Payment Status",
        "new_value": status,
        "synced_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "confirmation": f"GHL deal updated: Payment Status set to '{status}' for {invoice_id}",
    }


if __name__ == "__main__":
    sample_deal = {
        "deal_name": "Acme Corp - Website Redesign",
        "amount": 4200,
        "client_name": "Acme Corp",
        "deal_id": "DEAL-001",
    }

    print("=== Success path ===")
    result = sync_deal_won(sample_deal, simulate_failure=False)
    for line in result["sync_log"]:
        print(line)

    print("\n=== Simulated failure + retry path ===")
    result_fail = sync_deal_won(sample_deal, simulate_failure=True)
    for line in result_fail["sync_log"]:
        print(line)
