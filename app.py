import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(page_title="Shaker Health Dashboard", layout="wide")
st.title("🛠️ Real-Time Shaker Monitoring Dashboard")

# Sidebar setup
SCREEN_MESH_CAPACITY = {
    "API 100": 250,
    "API 140": 200,
    "API 170": 160,
    "API 200": 120
}
df_mesh_type = st.sidebar.selectbox("Select Screen Mesh Type", list(SCREEN_MESH_CAPACITY.keys()))
mesh_capacity = SCREEN_MESH_CAPACITY[df_mesh_type]
util_threshold = st.sidebar.slider("Util Threshold (%)", 50, 100, 80)

uploaded_file = st.file_uploader("📤 Upload Shaker CSV Data", type=["csv"])
if uploaded_file:
    df = pd.read_csv(uploaded_file)
    st.write("Columns in uploaded CSV:", df.columns.tolist())

    # Try Timestamp parsing
    try:
        df['Timestamp'] = pd.to_datetime(df['YYYY/MM/DD'] + ' ' + df['HH:MM:SS'])
        df = df.sort_values('Timestamp')
        df['Date'] = df['Timestamp'].dt.date
    except Exception as e:
        st.error(f"Timestamp creation failed: {e}")

    # Derive screen utilization if missing
    if 'Screen Utilization (%)' not in df.columns and 'Weight on Bit (klbs)' in df.columns and 'MA_Flow_Rate (gal/min)' in df.columns:
        df['Solids Volume Rate (gpm)'] = df['Weight on Bit (klbs)'] * df['MA_Flow_Rate (gal/min)'] / 100
        df['Screen Utilization (%)'] = (df['Solids Volume Rate (gpm)'] / mesh_capacity) * 100

    # Charts
    if 'SHAKER #1 (Units)' in df.columns and 'SHAKER #2 (Units)' in df.columns and 'SHAKER #3 (PERCENT)' in df.columns:
        fig2 = go.Figure()
        fig2.add_trace(go.Scatter(x=df['Timestamp'], y=df['SHAKER #1 (Units)'], mode='lines', name='SHAKER #1'))
        fig2.add_trace(go.Scatter(x=df['Timestamp'], y=df['SHAKER #2 (Units)'], mode='lines', name='SHAKER #2'))
        fig2.add_trace(go.Scatter(x=df['Timestamp'], y=df['SHAKER #3 (PERCENT)'], mode='lines', name='SHAKER #3'))
        fig2.update_layout(title='Shaker Output Over Time')
        st.plotly_chart(fig2, use_container_width=True)

    if 'MA_Flow_Rate (gal/min)' in df.columns:
        fig3 = px.line(df, x='Timestamp', y='MA_Flow_Rate (gal/min)', title='Flow Rate Over Time')
        st.plotly_chart(fig3, use_container_width=True)

    # Daily averages + validation
    try:
        daily_avg = df.groupby('Date').agg({
            'Screen Utilization (%)': 'mean',
            'MA_Flow_Rate (gal/min)': 'mean',
            'SHAKER #3 (PERCENT)': ['mean', 'max']
        }).reset_index()
        daily_avg.columns = ['Date', 'Avg Utilization', 'Avg Flow Rate', 'Avg SHKR3', 'Max SHKR3']
        daily_avg['Exceeds Threshold'] = daily_avg['Avg Utilization'] > util_threshold

        st.subheader("🔍 Daily Averages, Thresholds & Outliers")
        fig4 = px.bar(daily_avg, x='Date', y='Avg Utilization', color='Exceeds Threshold',
                      color_discrete_map={True: 'red', False: 'green'})
        st.plotly_chart(fig4, use_container_width=True)

        fig5 = px.box(df, x='Date', y='SHAKER #3 (PERCENT)', title='SHAKER #3 Outlier Distribution by Day')
        st.plotly_chart(fig5, use_container_width=True)

        if st.checkbox("Show Daily Average Data Table"):
            st.dataframe(daily_avg)

    except KeyError as e:
        st.warning(f"Skipping daily average plot due to missing column: {e}")
        st.write("Available columns:", df.columns.tolist())
else:
    st.info("Please upload a valid CSV to begin.")
