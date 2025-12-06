import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import json
import os

# --- PAGE CONFIG ---
st.set_page_config(
    page_title="S&T Index Boardroom",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- LOAD ASSETS ---
def load_css(file_name):
    with open(file_name) as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

try:
    # Adjust path if running locally from root
    css_path = os.path.join(os.path.dirname(__file__), 'assets/style.css')
    load_css(css_path)
except FileNotFoundError:
    st.warning("CSS file not found.")

# --- LOAD DATA ---
@st.cache_data
def load_data():
    # Adjust path
    base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_path = os.path.join(base_path, 'data')
    processed_path = os.path.join(data_path, 'processed_index.csv')
    return pd.read_csv(processed_path)

@st.cache_data
def load_debates():
    base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    assets_path = os.path.join(base_path, 'app', 'assets')
    json_path = os.path.join(assets_path, 'ai_debates.json')
    with open(json_path, 'r', encoding='utf-8') as f:
        return json.load(f)

try:
    df = load_data()
    debates = load_debates()
except Exception as e:
    st.error(f"Error loading data: {e}")
    st.stop()

# --- SIDEBAR ---
with st.sidebar:
    st.image("https://via.placeholder.com/150x50?text=PKO+Mock+Logo", use_container_width=True) # Replace with real logo if available
    st.title("S&T Dashboard")
    st.write("Wersja 3.0 (Hackathon)")
    
    st.divider()
    
    selected_sector = st.selectbox("Wybierz Sektor:", ["Wszystkie"] + list(df['Sector'].unique()))
    
    if selected_sector != "Wszystkie":
        filtered_df = df[df['Sector'] == selected_sector]
    else:
        filtered_df = df

    st.info("💡 **Instrukcja:** Kliknij w bąbelek na wykresie, aby zobaczyć debatę Zarządu.")

# --- MAIN LAYOUT ---
st.title("S&T Index (Stability & Transformation)")
st.markdown("### `System Diagnostyki Branżowej AI PKO BP`")

col_main, col_details = st.columns([2, 1])

# --- CHART (LEFT) ---
with col_main:
    # Create Bubble Chart using Plotly Graph Objects for more control
    fig = go.Figure()

    # Color mapping for Status
    color_map = {
        'CRITICAL': '#ff4b4b',
        'OPPORTUNITY': '#2ecc71',
        'Neutral': '#3498db'
    }

    # Add traces for different statuses to allow legend
    for status in df['Status'].unique():
        subset = filtered_df[filtered_df['Status'] == status]
        fig.add_trace(go.Scatter(
            x=subset['Stability_Score'],
            y=subset['Transformation_Score'],
            mode='markers+text',
            text=subset['Industry_Name'].str[:20] + "...", # Truncate for label
            textposition="top center",
            marker=dict(
                size=subset['Revenue_2024'] / subset['Revenue_2024'].max() * 60 + 10, # Size by Revenue
                color=color_map.get(status, '#888'),
                opacity=0.8,
                line=dict(width=1, color='white')
            ),
            name=status,
            customdata=subset[['Industry_Name', 'Revenue_2024', 'PKD_Code', 'Profitability']],
            hovertemplate="<b>%{customdata[0]}</b><br>" +
                          "PKD: %{customdata[2]}<br>" +
                          "Stability: %{x:.1f}<br>" +
                          "Transformation: %{y:.1f}<br>" +
                          "Revenue: %{customdata[1]:,.0f} PLN<extra></extra>"
        ))
        
    # Draw Quadrant Lines
    fig.add_hline(y=50, line_dash="dash", line_color="gray", annotation_text="Transformation Threshold")
    fig.add_vline(x=50, line_dash="dash", line_color="gray", annotation_text="Stability Threshold")

    # Add "Vectors" (Simple arrows for selected top industries to reduce clutter)
    # Ideally logic would be based on Google Trends Slope -> Future position
    # Here we can add a few illustrative arrows if needed, but for MVP keep it simple bubbles.

    fig.update_layout(
        xaxis_title="Stability Score (Fundament)",
        yaxis_title="Transformation Score (Potencjał)",
        xaxis=dict(range=[0, 100]),
        yaxis=dict(range=[0, 100]),
        height=700,
        legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color="white")
    )

    # Display Chart
    # Use selection event to capture clicks (Streamlit 1.30+ supports this better via on_select components or simple key hack)
    # We will use keys for selection simulation in MVP
    
    st.plotly_chart(fig, use_container_width=True, key="bubble_chart", on_select="rerun", selection_mode="points")


# --- DETAILS (RIGHT) ---
with col_details:
    st.subheader("AI Boardroom")
    
    # Check if a point is selected
    selection = st.session_state.get("bubble_chart", {}).get("selection", {}).get("points", [])
    
    if selection:
        # Get index of selected point
        # Plotly returns curveNumber and pointIndex. 
        # We need to map it back to the dataframe. 
        # Since we have multiple traces, it's a bit tricky. 
        # Easier strategy for hackathon: Filtered DF is the source of truth order if 1 trace, but we have multiple.
        
        # Simple hack: find the row in original filtered_df that matches the x/y
        point = selection[0]
        x_val = point['x']
        y_val = point['y']
        
        # Find exact match (float comparison might be risky, use approx)
        selected_row = filtered_df[
            (abs(filtered_df['Stability_Score'] - x_val) < 0.001) & 
            (abs(filtered_df['Transformation_Score'] - y_val) < 0.001)
        ].iloc[0]
        
        industry_name = selected_row['Industry_Name']
        pkd_code = str(selected_row['PKD_Code'])
        
        st.markdown(f"#### {industry_name} `(PKD {pkd_code})`")
        
        # Metrics Row
        m1, m2 = st.columns(2)
        m1.metric("Stability", f"{selected_row['Stability_Score']:.1f}", delta_color="normal")
        m2.metric("Transformation", f"{selected_row['Transformation_Score']:.1f}", delta_color="normal")
        
        st.divider()
        
        # Debate Content
        debate = debates.get(pkd_code)
        
        if debate:
            # CRO
            st.markdown(f"""
            <div class="cro-bubble">
                <strong>👩‍💼 CRO (Ryzyko):</strong><br>
                "{debate['CRO_Opinion']}"
            </div>
            """, unsafe_allow_html=True)
            
            # CSO
            st.markdown(f"""
            <div class="cso-bubble">
                <strong>🚀 CSO (Strategia):</strong><br>
                "{debate['CSO_Opinion']}"
            </div>
            """, unsafe_allow_html=True)
            
            # Verdict
            verdict = debate['Final_Verdict']
            v_class = "verdict-hold"
            if verdict == "BUY": v_class = "verdict-buy"
            if verdict == "REJECT": v_class = "verdict-reject"
            
            st.markdown(f"""
            <div class="verdict-box {v_class}">
                WERDYKT: {verdict}
            </div>
            """, unsafe_allow_html=True)
            
        else:
            st.info("Brak danych debaty dla tej branży.")
            
    else:
        st.write("👈 Wybierz branżę na wykresie, aby podsłuchać debatę zarządu.")
        st.image("https://media.giphy.com/media/l0HlHFRbmaZtBRhXG/giphy.gif") # Placeholder generic business gif
