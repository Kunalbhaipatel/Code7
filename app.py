import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(page_title="Shaker Health Dashboard", layout="wide")
st.markdown("""
    <style>
        .main {background-color: #f9f9f9; padding: 20px;}
        .css-18e3th9 {padding: 1rem;}
        h1, h2, h3, h4 {color: #2E86AB;}
        .stMetric {background-color: #ffffff; border: 1px solid #ddd; border-radius: 5px; padding: 10px;}
    </style>
""", unsafe_allow_html=True)

st.title("🛠️ Real-Time Shaker Monitoring Dashboard")

SCREEN_MESH_CAPACITY = {
    "API 100": 250,
    "API 140": 200,
    "API 170": 160,
    "API 200": 120
}

df_mesh_type = st.sidebar.selectbox("Select Screen Mesh Type", list(SCREEN_MESH_CAPACITY.keys()))
mesh_capacity = SCREEN_MESH_CAPACITY[df_mesh_type]
util_threshold = st.sidebar.slider("Utilization Threshold (%)", 50, 100, 80)

uploaded_file = st.file_uploader("📤 Upload Shaker CSV Data", type=["csv"])
if uploaded_file:
    df = pd.read_csv(uploaded_file)
    st.markdown("### ✅ CSV Successfully Loaded")
    st.write(df.head())

    try:
        df['Timestamp'] = pd.to_datetime(df['YYYY/MM/DD'] + ' ' + df['HH:MM:SS'])
        df = df.sort_values('Timestamp')
        df['Date'] = df['Timestamp'].dt.date
    except Exception as e:
        st.error(f"Timestamp parsing failed: {e}")

    if 'Screen Utilization (%)' not in df.columns and 'Weight on Bit (klbs)' in df.columns and 'MA_Flow_Rate (gal/min)' in df.columns:
        df['Solids Volume Rate (gpm)'] = df['Weight on Bit (klbs)'] * df['MA_Flow_Rate (gal/min)'] / 100
        df['Screen Utilization (%)'] = (df['Solids Volume Rate (gpm)'] / mesh_capacity) * 100

    # KPI Row
    st.subheader("📊 Key Metrics")
    avg_util = df['Screen Utilization (%)'].mean() if 'Screen Utilization (%)' in df.columns else 0
    avg_flow = df['MA_Flow_Rate (gal/min)'].mean() if 'MA_Flow_Rate (gal/min)' in df.columns else 0
    shaker_max = df['SHAKER #3 (PERCENT)'].max() if 'SHAKER #3 (PERCENT)' in df.columns else 0
    colk1, colk2, colk3 = st.columns(3)
    colk1.metric("Avg Utilization", f"{avg_util:.1f}%", delta=None)
    colk2.metric("Avg Flow Rate", f"{avg_flow:.1f} gpm", delta=None)
    colk3.metric("Max SHKR3", f"{shaker_max:.1f}%", delta=None)

    tab1, tab2 = st.tabs(["📈 Charts", "📋 Raw Data"])

    with tab1:
        st.subheader("📈 Shaker Output Over Time")
        if {'SHAKER #1 (Units)', 'SHAKER #2 (Units)', 'SHAKER #3 (PERCENT)'}.issubset(df.columns):
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=df['Timestamp'], y=df['SHAKER #1 (Units)'], mode='lines', name='SHAKER #1'))
            fig.add_trace(go.Scatter(x=df['Timestamp'], y=df['SHAKER #2 (Units)'], mode='lines', name='SHAKER #2'))
            fig.add_trace(go.Scatter(x=df['Timestamp'], y=df['SHAKER #3 (PERCENT)'], mode='lines', name='SHAKER #3'))
            fig.update_layout(margin=dict(l=40, r=40, t=40, b=40))
            st.plotly_chart(fig, use_container_width=True)

        if 'MA_Flow_Rate (gal/min)' in df.columns:
            st.subheader("💧 Flow Rate Over Time")
            flow_chart = px.line(df, x='Timestamp', y='MA_Flow_Rate (gal/min)')
            st.plotly_chart(flow_chart, use_container_width=True)

        try:
            daily_avg = df.groupby('Date').agg({
                'Screen Utilization (%)': 'mean',
                'MA_Flow_Rate (gal/min)': 'mean',
                'SHAKER #3 (PERCENT)': ['mean', 'max']
            }).reset_index()
            daily_avg.columns = ['Date', 'Avg Utilization', 'Avg Flow Rate', 'Avg SHKR3', 'Max SHKR3']
            daily_avg['Exceeds Threshold'] = daily_avg['Avg Utilization'] > util_threshold

            st.subheader("📊 Daily Summary Analysis")
            col1, col2 = st.columns(2)
            with col1:
                bar_chart = px.bar(daily_avg, x='Date', y='Avg Utilization', color='Exceeds Threshold',
                                color_discrete_map={True: 'red', False: 'green'})
                st.plotly_chart(bar_chart, use_container_width=True)
            with col2:
                box_chart = px.box(df, x='Date', y='SHAKER #3 (PERCENT)')
                st.plotly_chart(box_chart, use_container_width=True)

        except KeyError as e:
            st.warning(f"Missing column for daily average plot: {e}")
            st.write("Available columns:", df.columns.tolist())

    with tab2:
        st.subheader("📄 Full Dataset")
        st.dataframe(df)

else:
    st.info("Please upload a valid CSV to begin analysis.")
