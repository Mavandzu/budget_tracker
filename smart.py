#!/usr/bin/env python
# coding: utf-8

# In[4]:


import streamlit as st
import pandas as pd
import datetime

st.set_page_config(page_title="Smart Budget Tracker", layout="wide")

st.title("💰 Smart Budget Tracker")

# --- Initialize Session State ---
if "transactions" not in st.session_state:
    st.session_state["transactions"] = pd.DataFrame(columns=["Date", "Category", "Amount", "Note"])

# --- Sidebar for Input ---
st.sidebar.header("Add Expense / Income")

with st.sidebar.form("transaction_form", clear_on_submit=True):
    date = st.date_input("Date", datetime.date.today())
    category = st.selectbox("Category", ["Food", "Transport", "Rent", "Utilities", "Entertainment", "Income", "Other"])
    amount = st.number_input("Amount (R)", step=1.0, format="%.2f")
    note = st.text_input("Note (optional)")
    submitted = st.form_submit_button("Add Transaction")

    if submitted:
        new_row = pd.DataFrame([[date, category, amount, note]], 
                               columns=["Date", "Category", "Amount", "Note"])
        st.session_state["transactions"] = pd.concat([st.session_state["transactions"], new_row], ignore_index=True)
        st.success("Transaction added!")

# --- Import Transactions from CSV ---
st.sidebar.header("📥 Import CSV")
uploaded_file = st.sidebar.file_uploader("Upload a CSV file", type=["csv"])

if uploaded_file is not None:
    try:
        # Handle semicolon-separated and comma-separated CSVs
        try:
            imported_df = pd.read_csv(uploaded_file, sep=";")
        except Exception:
            imported_df = pd.read_csv(uploaded_file)

        # Normalize Date column if it exists
        if "Date" in imported_df.columns:
            imported_df["Date"] = pd.to_datetime(imported_df["Date"], errors="coerce")

        expected_cols = ["Date", "Category", "Amount", "Note"]
        if all(col in imported_df.columns for col in expected_cols):
            st.session_state["transactions"] = pd.concat(
                [st.session_state["transactions"], imported_df], ignore_index=True
            ).drop_duplicates().reset_index(drop=True)
            st.sidebar.success("Transactions imported successfully!")
        else:
            st.sidebar.error(f"CSV must have columns: {expected_cols}")
    except Exception as e:
        st.sidebar.error(f"Error reading CSV: {e}")


# --- Display Transactions ---
st.subheader("📊 Transaction History")
df = st.session_state["transactions"]
st.dataframe(df, use_container_width=True)

# --- Export Button ---
if not df.empty:
    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="⬇️ Export Transactions to CSV",
        data=csv,
        file_name="transactions.csv",
        mime="text/csv",
    )

# --- Budget Setup ---
st.subheader("📅 Monthly Budget")
monthly_budget = st.number_input("Set Monthly Budget (R)", step=100.0, format="%.2f")

# --- Analytics ---
if not df.empty:
    expenses = df[df["Category"] != "Income"]
    income = df[df["Category"] == "Income"]["Amount"].sum()
    total_expenses = expenses["Amount"].sum()
    balance = income - total_expenses if income > 0 else monthly_budget - total_expenses

    st.metric("Total Expenses", f"R {total_expenses:,.2f}")
    st.metric("Total Income", f"R {income:,.2f}")
    st.metric("Balance", f"R {balance:,.2f}")

    # --- Category breakdown ---
    st.subheader("📌 Spending by Category")
    cat_summary = expenses.groupby("Category")["Amount"].sum().reset_index()
    st.bar_chart(cat_summary.set_index("Category"))

    # --- Smart Suggestions ---
    st.subheader("💡 Suggestions")
    suggestions = []
    if total_expenses > monthly_budget:
        suggestions.append("⚠️ You are **over budget**. Reduce non-essential expenses like Entertainment.")
    elif total_expenses > 0.8 * monthly_budget:
        suggestions.append("⚠️ You're nearing your budget limit. Cut down on eating out or subscriptions.")
    else:
        suggestions.append("✅ Great job staying within budget!")

    if income > 0 and (total_expenses < income * 0.7):
        suggestions.append("💾 You’re saving well! Consider moving extra cash into investments or savings.")

    if "Food" in cat_summary["Category"].values:
        food_spend = cat_summary.loc[cat_summary["Category"] == "Food", "Amount"].values[0]
        if food_spend > 0.3 * total_expenses:
            suggestions.append("🍔 Food expenses are high. Try meal prepping to save money.")

    for s in suggestions:
        st.write(s)
else:
    st.info("No transactions yet. Add your first expense or income on the left.")

