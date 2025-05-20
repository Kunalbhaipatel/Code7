import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# Constants
SCREEN_MESH_CAPACITY = {
    "API 100": 250,
    "API 140": 200,
    "API 170": 160,
    "API 200": 120
}
EXPECTED_SCREEN_LIFE_HRS = 120

st.set_page_config(page_title="Shaker Health Dashboard", layout="wide")
st.title("🛠️ Real-Time Shaker Monitoring Dashboard")

# Sidebar configuration
df_mesh_type = st.sidebar.selectbox("Select Screen Mesh Type", list(SCREEN_MESH_CAPACITY.keys()), index=0)
mesh_capacity = SCREEN_MESH_CAPACITY[df_mesh_type]

# File uploader
uploaded_file = st.file_uploader("Upload Shaker CSV Data", type=["csv"])

if uploaded_file:
    df = pd.read_csv(uploaded_file)

    # Filter only necessary columns
    required_cols = [
        'YYYY/MM/DD', 'HH:MM:SS', 'Hole Depth (feet)', 'Bit Depth (feet)', 'Hook Load (klbs)',
        'Total Mud Volume (barrels)', 'Weight on Bit (klbs)', 'SHAKER #1 (Units)', 'Tool Face (degrees)',
        'SHAKER #2 (Units)', 'SHAKER #3 (PERCENT)', 'Heavy Ratio (percent)',
        'PVT Monitor Mud Gain/Loss (barrels)', 'Total Mud Low Warning (barrels)',
        'Flow Low Warning (flow_percent)', 'Flow High Warning (flow_percent)',
        'Trip Mud High Warning (barrels)', 'MA_Temp (degF)', 'MA_Flow_Rate (gal/min)',
        'Site Mud Volume (barrels)', 'Inactive Mud Volume (barrels)'
    ]
    df = df[required_cols]

    # Time column for plotting
    df['Timestamp'] = pd.to_datetime(df['YYYY/MM/DD'] + ' ' + df['HH:MM:SS'])
    df = df.sort_values('Timestamp')

    # Tab Layout
    tab1, tab2 = st.tabs(["📋 Summary", "📈 Charts"])

    with tab1:
        st.subheader("📊 Summary Insights")

        # --- 1. Screen Utilization ---
        df['Solids Volume Rate (gpm)'] = df['Weight on Bit (klbs)'] * df['MA_Flow_Rate (gal/min)'] / 100
        df['Screen Utilization (%)'] = (df['Solids Volume Rate (gpm)'] / mesh_capacity) * 100
        avg_util = df['Screen Utilization (%)'].mean()
        st.metric("Average Screen Utilization", f"{avg_util:.2f}%")

        # --- 2. Screen Life Estimation ---
        df['ROP Proxy'] = df['Weight on Bit (klbs)'] * df['MA_Flow_Rate (gal/min)']
        usage_factor = df['ROP Proxy'].mean() / 1000
        est_life_used = usage_factor * 10
        remaining_life = max(EXPECTED_SCREEN_LIFE_HRS - est_life_used, 0)
        st.metric("Estimated Remaining Screen Life", f"{remaining_life:.1f} hrs")

        # --- 3. G-Force Drop Detector ---
        drop_detected = ((df['SHAKER #3 (PERCENT)'].diff().abs() > 10) & (df['MA_Flow_Rate (gal/min)'].diff().abs() < 2)).any()
        g_status = "🔴 DROP DETECTED!" if drop_detected else "🟢 Stable"
        st.metric("Shaker G-Force Health", g_status)

    with tab2:
        st.subheader("📈 Time-Series Analytics")

        fig1, ax1 = plt.subplots()
        ax1.plot(df['Timestamp'], df['Screen Utilization (%)'], label='Utilization', color='blue')
        ax1.set_ylabel('% Utilization')
        ax1.set_xlabel('Time')
        ax1.set_title('Screen Utilization Over Time')
        ax1.grid(True)
        st.pyplot(fig1)

        fig2, ax2 = plt.subplots()
        ax2.plot(df['Timestamp'], df['SHAKER #1 (Units)'], label='SHAKER #1', alpha=0.8)
        ax2.plot(df['Timestamp'], df['SHAKER #2 (Units)'], label='SHAKER #2', alpha=0.8)
        ax2.plot(df['Timestamp'], df['SHAKER #3 (PERCENT)'], label='SHAKER #3', alpha=0.8)
        ax2.legend()
        ax2.set_title("Shaker Outputs")
        ax2.set_xlabel("Time")
        ax2.grid(True)
        st.pyplot(fig2)

        fig3, ax3 = plt.subplots()
        ax3.plot(df['Timestamp'], df['MA_Flow_Rate (gal/min)'], label='Flow Rate')
        ax3.set_title("Flow Rate Over Time")
        ax3.set_ylabel("GPM")
        ax3.grid(True)
        st.pyplot(fig3)

else:
    st.info("Please upload a valid CSV with required fields.")
