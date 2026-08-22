import streamlit as st
import pandas as pd
from sqlalchemy import create_engine

# Page Configuration
st.set_page_config(
    page_title="Bank Reconciliation Engine", 
    page_icon="🏦", 
    layout="wide"
)

# Custom CSS for Modern UI
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stMetric {
        background-color: #ffffff;
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        border: 1px solid #e9ecef;
    }
    .status-badge {
        font-weight: bold;
        padding: 4px 8px;
        border-radius: 6px;
    }
    </style>
""", unsafe_allow_html=True)

# Database Connection
engine = create_engine('postgresql://postgres:root@localhost:5433/bank_reconciliation')

# Header
st.title("🏦 Automated Bank Reconciliation Engine")
st.caption("Real-time discrepancy detection & automated ledger matching pipeline")
st.markdown("---")

query = """
SELECT 
    COALESCE(l.reference_no, b.reference_no) AS reference_no,
    l.amount AS ledger_amount,
    b.amount AS bank_amount,
    l.date AS ledger_date,
    b.date AS bank_date,
    CASE 
        WHEN l.reference_no IS NULL THEN 'MISSING_IN_LEDGER'
        WHEN b.reference_no IS NULL THEN 'MISSING_IN_BANK'
        WHEN l.amount != b.amount THEN 'AMOUNT_MISMATCH'
        ELSE 'EXACT_MATCH'
    END AS reconciliation_status
FROM internal_ledger l
FULL OUTER JOIN bank_statement b ON l.reference_no = b.reference_no;
"""

try:
    df = pd.read_sql(query, engine)

    # Key Metrics Section
    col1, col2, col3, col4 = st.columns(4)
    
    total_txns = len(df)
    exact_matches = len(df[df['reconciliation_status'] == 'EXACT_MATCH'])
    mismatches = len(df[df['reconciliation_status'] == 'AMOUNT_MISMATCH'])
    missing = len(df[df['reconciliation_status'].str.contains('MISSING')])

    col1.metric("Total Transactions", f"{total_txns:,}")
    col2.metric("Exact Matches ✅", f"{exact_matches:,}", f"{(exact_matches/total_txns)*100:.1f}%")
    col3.metric("Amount Mismatches ⚠️", f"{mismatches:,}", f"-{(mismatches/total_txns)*100:.1f}%", delta_color="inverse")
    col4.metric("Missing Entries ❌", f"{missing:,}", f"-{(missing/total_txns)*100:.1f}%", delta_color="inverse")

    st.markdown("###")

    # Sidebar / Main Filters
    st.subheader("🔍 Filter & Inspect Discrepancies")
    
    selected_status = st.selectbox(
        "Select Status to Filter:", 
        options=['ALL'] + list(df['reconciliation_status'].unique()),
        index=0
    )

    if selected_status != 'ALL':
        filtered_df = df[df['reconciliation_status'] == selected_status]
    else:
        filtered_df = df

    st.markdown(f"Displaying **{len(filtered_df):,}** records")

    # Data Table with Formatting
    st.dataframe(
        filtered_df, 
        use_container_width=True,
        column_config={
            "reference_no": "Reference No",
            "ledger_amount": st.column_config.NumberColumn("Ledger Amount ($)", format="$%.2f"),
            "bank_amount": st.column_config.NumberColumn("Bank Amount ($)", format="$%.2f"),
            "ledger_date": "Ledger Date",
            "bank_date": "Bank Date",
            "reconciliation_status": "Status"
        },
        hide_index=True
    )

except Exception as e:
    st.error(f"⚠️ Connection Error: {e}")