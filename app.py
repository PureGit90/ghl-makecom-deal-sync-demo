import streamlit as st

from sync_pipeline import sync_deal_won, sync_payment_status_back

st.set_page_config(page_title="Deal-Won Sync Pipeline", page_icon="🔄", layout="centered")

st.title("Deal-Won Sync Pipeline")
st.write("Simulates a GoHighLevel 'deal won' webhook fanning out to invoicing, project management, and Google Sheets -- with retry logic and failure alerting on every step.")

st.divider()

st.subheader("1. Simulate a GHL 'Deal Won' Webhook")

with st.form("deal_form"):
    deal_name = st.text_input("Deal Name", value="Acme Corp - Website Redesign")
    amount = st.number_input("Amount ($)", min_value=0, value=4200, step=100)
    client_name = st.text_input("Client Name", value="Acme Corp")
    simulate_failure = st.checkbox("Simulate a step failure (to show retry/error handling)")
    submitted = st.form_submit_button("Trigger Sync")

if submitted:
    deal_payload = {
        "deal_name": deal_name,
        "amount": amount,
        "client_name": client_name,
        "deal_id": f"DEAL-{abs(hash(deal_name)) % 10000}",
    }

    result = sync_deal_won(deal_payload, simulate_failure=simulate_failure)

    st.subheader("Sync Results")

    status_icons = {
        "success": "✅",
        "retried-then-success": "🔁",
        "failed": "❌",
    }
    for step in result["steps"]:
        icon = status_icons.get(step["status"], "•")
        st.write(f"{icon} **{step['step']}** -- {step['status'].replace('-', ' ')}")

    with st.expander("Full sync log", expanded=True):
        st.code("\n".join(result["sync_log"]), language=None)

    st.subheader("Resulting Records")
    records = result["records"]
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("**Invoice**")
        st.json(records.get("invoice") or {"status": "not created"})
    with col2:
        st.markdown("**Project Card**")
        st.json(records.get("project") or {"status": "not created"})
    with col3:
        st.markdown("**Sheet Row**")
        st.json(records.get("sheet_row") or {"status": "not created"})

    st.caption("Sample sync -- connect your GoHighLevel and Make.com credentials for live automation.")

    if records.get("invoice"):
        st.session_state["last_invoice_id"] = records["invoice"]["invoice_id"]

st.divider()

st.subheader("2. Reverse Sync: Payment Status Back to GHL")
st.write("When the invoice is marked paid in the invoicing platform, the payment status syncs back into the GHL deal record automatically.")

default_invoice_id = st.session_state.get("last_invoice_id", "INV-DEMO1234")
invoice_id_input = st.text_input("Invoice ID", value=default_invoice_id)

if st.button("Mark Invoice Paid"):
    confirmation = sync_payment_status_back(invoice_id_input, "Paid")
    st.success(confirmation["confirmation"])
    st.json(confirmation)
    st.caption("Sample sync -- connect your GoHighLevel and Make.com credentials for live automation.")
