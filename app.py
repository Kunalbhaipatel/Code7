import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from PIL import Image

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
util_threshold = st.sidebar.slider("Set Utilization Alert Threshold (%)", min_value=50, max_value=100, value=80, step=1)

# Visual Icons/Images
col1, col2 = st.columns(2)
with col1:
    st.image("HyperPool_silo_800X600-1.png.png", caption="Shaker Screen", use_container_width=True)
with col2:
    st.image("Hyperpool_SideView_Compression1_LR-removebg-preview (1).png", caption="Shaker Unit", use_container_width=True)

        fig2 = go.Figure()
        fig2.add_trace(go.Scatter(x=df['Timestamp'], y=df['SHAKER #1 (Units)'], mode='lines', name='SHAKER #1'))
        fig2.add_trace(go.Scatter(x=df['Timestamp'], y=df['SHAKER #2 (Units)'], mode='lines', name='SHAKER #2'))
        fig2.add_trace(go.Scatter(x=df['Timestamp'], y=df['SHAKER #3 (PERCENT)'], mode='lines', name='SHAKER #3'))
        fig2.update_layout(title='Shaker Output Over Time', xaxis_title='Time', yaxis_title='Shaker Output')
        st.plotly_chart(fig2, use_container_width=True)

        fig3 = px.line(df, x='Timestamp', y='MA_Flow_Rate (gal/min)', title='Flow Rate Over Time')
        st.plotly_chart(fig3, use_container_width=True)

        st.subheader("🔍 Daily Averages, Thresholds & Outliers")
        daily_avg = df.groupby('Date').agg({
            'Screen Utilization (%)': 'mean',
            'MA_Flow_Rate (gal/min)': 'mean',
            'SHAKER #3 (PERCENT)': ['mean', 'max']
        }).reset_index()
        daily_avg.columns = ['Date', 'Avg Utilization', 'Avg Flow Rate', 'Avg SHKR3', 'Max SHKR3']
        daily_avg['Exceeds Threshold'] = daily_avg['Avg Utilization'] > util_threshold

        fig4 = px.bar(daily_avg, x='Date', y='Avg Utilization', color='Exceeds Threshold',
                      color_discrete_map={True: 'red', False: 'green'},
                      title=f'Daily Avg Screen Utilization vs {util_threshold}% Threshold')
        st.plotly_chart(fig4, use_container_width=True)

        fig5 = px.box(df, x='Date', y='SHAKER #3 (PERCENT)', title='SHAKER #3 Outlier Distribution by Day')
        st.plotly_chart(fig5, use_container_width=True)

        st.markdown("""
        📋 **Explore the Daily Averages Table**  
        This table shows daily average screen utilization, flow rate, and shaker output to help you spot high-load days, efficiency dips, or operational inconsistencies.
        """)
        if st.checkbox("Show Daily Average Data Table"):
            st.dataframe(daily_avg)

else:
    st.info("Please upload a valid CSV with required fields.")
