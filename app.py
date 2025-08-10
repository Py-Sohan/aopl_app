import pandas as pd
import streamlit as st
import plotly.express as px
from datetime import datetime, timedelta

# Load data (from path)
df = pd.read_excel('files/dealer_app.xlsx', sheet_name='Sheet1')
df['Visit DateTime'] = pd.to_datetime(df['Date'].astype(str) + ' ' + df['Time'].astype(str))
df['Visit Date'] = df['Visit DateTime'].dt.date

# Sidebar Filters
st.sidebar.title("🔍 Filters")

# Date Range Presets
today = df['Visit Date'].max()
last_day = today - timedelta(days=1)
last_7 = today - timedelta(days=7)
last_month = today - timedelta(days=30)

preset = st.sidebar.selectbox("Select Date Range", ["Last Day", "Last 7 Days", "Last Month", "Custom Range"])

if preset == "Last Day":
    start_date = last_day
    end_date = today
elif preset == "Last 7 Days":
    start_date = last_7
    end_date = today
elif preset == "Last Month":
    start_date = last_month
    end_date = today
else:
    start_date = st.sidebar.date_input("Start Date", min_value=min(df['Visit Date']), value=last_7)
    end_date = st.sidebar.date_input("End Date", max_value=max(df['Visit Date']), value=today)

# Staff Filter
staff_id_filter = st.sidebar.selectbox("Select Staff ID", df['Staff ID'].unique())
staff_df = df[(df['Staff ID'] == staff_id_filter) & (df['Visit Date'] >= start_date) & (df['Visit Date'] <= end_date)].copy()

# Detect Fake Visits (within 10 minutes)
staff_df = staff_df.sort_values(by='Visit DateTime')
staff_df['Time Diff'] = staff_df['Visit DateTime'].diff().dt.total_seconds().div(60).fillna(0)
staff_df['Is Fake'] = staff_df['Time Diff'] < 10

# Report Generation
report_df = staff_df.groupby(['Staff Name', 'Visit Date']).agg(
    Total_Visits=('FollowUpID', 'count'),
    Plumber_Visit=('Visit Type', lambda x: (x == 'Plumber Visit').sum()),
    Retailer_Visit=('Visit Type', lambda x: (x == 'Retailer Visit').sum()),
    Dealer_Visit=('Visit Type', lambda x: (x == 'Dealer Visit').sum()),
    Fake_Visits=('Is Fake', 'sum'),
    Visit_IDs=('FollowUpID', lambda x: ', '.join(map(str, x[staff_df.loc[x.index, 'Is Fake']])))
).reset_index()

report_df['% Fake Visits'] = ((report_df['Fake_Visits'] / report_df['Total_Visits']) * 100).round(1).astype(str) + '%'

# Rename columns for display
report_df.columns = ["Staff Name", "Date", "Total Visits", "Plumber Visit", "Retailer Visit", "Dealer Visit", "Fake Visits", "Visit IDs (Fake)", "% Fake Visits"]

# --- MAIN UI ---
st.title("🧑‍💼 Staff Visit Performance Dashboard")
st.markdown("View staff visit performance and detect fake visits based on time gaps.")

# Show report table
st.subheader("📋 Visit Summary Report")
st.dataframe(report_df)

# --- DETAILED FAKE VISIT TABLE ---
st.subheader("📍 Fake Visit Summary")

fake_visits_df = staff_df[staff_df['Is Fake']].copy()

if not fake_visits_df.empty:
    fake_visits_df['Visit Time'] = fake_visits_df['Visit DateTime'].dt.time
    
    detailed_table = fake_visits_df[[
        'Visit Date',
        'Visit Time',
        'Dealer Name',
        'Visit Type',
        'Time Diff',
        'FollowUpID'
    ]].rename(columns={
        'Visit Date': 'Date',
        'Dealer Name': 'Client Name',
        'Visit Type': 'Visit Type',
        'Time Diff': 'Time Gap (min)',
        'FollowUpID': 'Visit ID'
    })

    st.dataframe(detailed_table)
else:
    st.info("✅ No fake visits found for this staff in the selected date range.")

# --- PLOTLY CHARTS ---
st.subheader("📈 Visit Analytics")

report_df['% Fake Visits (Numeric)'] = report_df['% Fake Visits'].str.replace('%', '').astype(float)

# 1. Total vs Fake Visits
fig1 = px.bar(
    report_df,
    x="Date",
    y=["Total Visits", "Fake Visits"],
    barmode='group',
    title="Total vs Fake Visits per Day",
    labels={"value": "Visits", "variable": "Visit Type"}
)
st.plotly_chart(fig1, use_container_width=True)

# 2. Fake Visit % Trend
fig2 = px.line(
    report_df,
    x="Date",
    y="% Fake Visits (Numeric)",
    title="Percentage of Fake Visits Over Time",
    markers=True,
    labels={"% Fake Visits (Numeric)": "% Fake Visits"}
)
st.plotly_chart(fig2, use_container_width=True)

# Footer
st.markdown("---")
st.caption("Built By Lutfor Rahman Shohan")
